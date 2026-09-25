"""Reuse the pinned State implementation with explicit task-interface migration."""

from __future__ import annotations

import contextlib
import copy
import io
from pathlib import Path
import sys

import numpy as np
import torch
from torch import nn


def load_features(path):
    features = torch.load(path, map_location="cpu", weights_only=True)
    # H1 var/gene_id identifies TAZ as ENSG00000102125 (TAFAZZIN),
    # explicitly distinct from WWTR1 / ENSG00000018408. Preserve output labels.
    if "TAZ" not in features and "TAFAZZIN" in features:
        features["TAZ"] = features["TAFAZZIN"]
    return features


def load_upstream(source: Path):
    # The published package eagerly imports its unused legacy VCI decoder. Make
    # that dependency lazy in the isolated upstream copy, retaining model math.
    decoder = source / "src/state/tx/models/decoders.py"
    text = decoder.read_text()
    eager = "from ...emb.finetune_decoder import Finetune\n"
    anchor = "        super().__init__()\n"
    if eager in text and "        from ...emb.finetune_decoder import Finetune\n" not in text:
        text = text.replace(eager, "", 1).replace(anchor, anchor + "        " + eager, 1)
        decoder.write_text(text)
    sys.path.insert(0, str(source / "src"))
    from state.tx.models.state_transition import StateTransitionPerturbationModel
    return StateTransitionPerturbationModel


def normalized_features(features, names):
    missing = sorted(set(names) - set(features) - {"non-targeting"})
    if missing:
        raise ValueError(f"Missing protein features: {missing}")
    width = next(iter(features.values())).numel()
    rows = []
    for name in names:
        if name == "non-targeting":
            rows.append(torch.zeros(width))
        else:
            value = features[name].detach().cpu().float().reshape(-1)
            if value.numel() != width or not torch.isfinite(value).all() or value.norm() == 0:
                raise ValueError(f"Invalid protein feature: {name}")
            rows.append(value / value.norm())
    return torch.stack(rows)


def load_parent_targets(path):
    with torch.serialization.safe_globals([np._core.multiarray.scalar, np.dtype, np.dtypes.StrDType, np.str_]):
        mapping = torch.load(path, map_location="cpu", weights_only=True)
    names = [None] * len(mapping)
    for name, value in mapping.items():
        if value.ndim != 1 or value.numel() != len(names) or int(torch.count_nonzero(value)) != 1 or float(value.sum()) != 1.0:
            raise ValueError(f"Invalid parent one-hot vector: {name}")
        index = int(value.argmax())
        if names[index] is not None:
            raise ValueError("Parent targets share an input coordinate")
        names[index] = str(name)
    if any(name is None for name in names):
        raise ValueError("Parent target coordinate is missing")
    return names


def build_model(upstream: Path, parent: Path, genes, features, parent_targets, seed=42):
    torch.manual_seed(seed)
    if load_parent_targets(parent.with_name("pert_onehot_map.pt")) != list(parent_targets):
        raise ValueError("Parent target input semantics differ from the experiment protocol")
    base = load_upstream(upstream)

    class AdaptedState(base):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.measurement_encoder = nn.Linear(self.input_dim, self.hidden_dim, bias=False)
            nn.init.zeros_(self.measurement_encoder.weight)
            self.register_buffer("measurement_mask", torch.ones(self.input_dim), persistent=False)

        def encode_basal_expression(self, expression):
            return super().encode_basal_expression(expression) + self.measurement_encoder(1 - self.measurement_mask)

    checkpoint = torch.load(parent, map_location="cpu", weights_only=False)
    old = checkpoint["state_dict"]
    params = copy.deepcopy(checkpoint["hyper_parameters"])
    old_genes = [str(value) for value in params["gene_names"]]
    params.update({
        "input_dim": len(genes), "output_dim": len(genes), "gene_dim": len(genes),
        "hvg_dim": len(genes), "gene_names": list(genes), "pert_dim": next(iter(features.values())).numel(),
        "batch_encoder": False, "batch_dim": None, "gene_decoder_bool": False,
        "decoder_cfg": None, "embed_key": None, "output_space": "gene",
        "freeze_pert_backbone": False, "log1p_from_raw_counts": False,
        "finetune_vci_decoder": False, "dropout": 0.0,
    })
    with contextlib.redirect_stdout(io.StringIO()):
        model = AdaptedState(**params)
    current = model.state_dict()
    migrated = []
    excluded_prefixes = ("basal_encoder.", "pert_encoder.", "project_out.")
    for name, value in old.items():
        if not name.startswith(excluded_prefixes) and name in current and current[name].shape == value.shape:
            current[name].copy_(value)
            migrated.append(name)

    positions = {name: index for index, name in enumerate(genes)}
    old_positions, new_positions = zip(*[(i, positions[name]) for i, name in enumerate(old_genes) if name in positions])
    # Keep the father's single-linear input/output modules and residual branch.
    if "basal_encoder.0.weight" not in old or "project_out.0.weight" not in old:
        raise ValueError("Unsupported parent interface; expected one-layer encoders")
    with torch.no_grad():
        model.basal_encoder[0].weight.zero_()
        model.basal_encoder[0].weight[:, list(new_positions)] = old["basal_encoder.0.weight"][:, list(old_positions)]
        model.basal_encoder[0].bias.copy_(old["basal_encoder.0.bias"])
        nn.init.normal_(model.project_out[0].weight, std=0.001)
        model.project_out[0].bias.fill_(0.1)  # ReLU must not start dead on new genes.
        model.project_out[0].weight[list(new_positions)] = old["project_out.0.weight"][list(old_positions)]
        model.project_out[0].bias[list(new_positions)] = old["project_out.0.bias"][list(old_positions)]

        # Distill the old per-target condition vectors into a continuous linear
        # adapter. This is shared initialization, using no held-out responses.
        common = [(i, name) for i, name in enumerate(parent_targets) if name in features]
        rows = normalized_features(features, [name for _, name in common]).double()
        old_weight = old["pert_encoder.0.weight"].double()
        if old_weight.shape[1] != len(parent_targets):
            raise ValueError("Parent target ordering does not match encoder width")
        ntc = parent_targets.index("non-targeting")
        offsets = old_weight[:, [i for i, _ in common]].T - old_weight[:, ntc]
        gram = rows @ rows.T
        ridge = 0.01
        coefficients = torch.linalg.solve(gram + ridge * torch.eye(len(rows), dtype=gram.dtype), offsets)
        weight = (rows.T @ coefficients).T.float()
        model.pert_encoder[0].weight.copy_(weight)
        model.pert_encoder[0].bias.copy_(old["pert_encoder.0.bias"] + old["pert_encoder.0.weight"][:, ntc])
        residual = (rows @ weight.double().T - offsets).square().mean().sqrt().item()

    report = {
        "parent": str(parent), "seed": seed, "parent_gene_count": len(old_genes),
        "gene_count": len(genes), "copied_gene_rows": len(new_positions),
        "exact_parameter_keys": migrated,
        "dropped_parent_keys": [key for key in old if key not in current],
        "protein_distillation_targets": len(common), "protein_distillation_ridge": ridge,
        "protein_distillation_rmse": residual,
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "output_space": "gene", "normalization": "log1p(CP10000) on measured gene axis",
        "parent_normalization_provenance": "not fully verified; both arms share the new preprocessing",
    }
    return model, report


def set_trainable(model, unfreeze):
    for name, parameter in model.named_parameters():
        if name.startswith("transformer_backbone."):
            parameter.requires_grad_(unfreeze and "embed_tokens" not in name)
        else:
            parameter.requires_grad_(True)


def expression_from_counts(counts):
    values = np.asarray(counts, dtype=np.float32)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Counts must be finite and non-negative")
    totals = values.sum(axis=-1, keepdims=True, dtype=np.float64)
    if (totals <= 0).any():
        raise ValueError("Empty cells are not supported")
    return np.log1p(values * (10000.0 / totals)).astype(np.float32)


def integer_counts(prediction, control_counts, supervised, rng):
    """Fixed count adapter; genes without supervision retain NTC weights."""
    prediction = np.asarray(prediction, dtype=np.float64)
    control_counts = np.asarray(control_counts)
    if prediction.shape != control_counts.shape:
        raise ValueError("Prediction/control axes differ")
    if not np.isfinite(prediction).all():
        raise ValueError("Non-finite model predictions")
    totals = control_counts.sum(axis=1, dtype=np.float64)
    if (totals <= 0).any() or (totals > 1_000_000).any() or not np.equal(totals, np.floor(totals)).all():
        raise ValueError("Control depths are outside the integer count contract")
    weights = np.expm1(np.clip(prediction, 0, np.log1p(10000.0)))
    baseline = control_counts * (10000.0 / totals[:, None])
    weights[:, ~np.asarray(supervised, dtype=bool)] = baseline[:, ~np.asarray(supervised, dtype=bool)]
    sums = weights.sum(axis=1)
    if (sums <= 0).any():
        raise ValueError("Model produced an empty count distribution")
    output = np.empty_like(control_counts, dtype=np.int32)
    for row in range(len(weights)):
        probabilities = weights[row] / sums[row]
        output[row] = rng.multinomial(int(totals[row]), probabilities)
    return output
