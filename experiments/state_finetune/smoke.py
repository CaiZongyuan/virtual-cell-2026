"""Real GPU forward/backward checks; this is not a biological evaluation."""

import argparse
import json
from pathlib import Path
import time

import h5py
import numpy as np
import torch

from data import gene_names, read_rows
from model import build_model, expression_from_counts, integer_counts, load_features, normalized_features, set_trainable


def main(work, root):
    torch.set_num_threads(6)
    protocol = json.loads((work / "protocol.json").read_text())
    features = load_features(root / "assets/ESM2_pert_features.pt")
    model, migration = build_model(work / "upstream/state", root / "assets/parent/best.ckpt",
                                   protocol["genes"], features, protocol["parent_targets"])
    positions = {gene: index for index, gene in enumerate(protocol["genes"])}
    control_path = next((work / "controls").rglob("*.h5ad"))
    with h5py.File(control_path) as handle:
        genes = gene_names(handle)
        selected = np.array([positions[gene] for gene in genes])
        raw = read_rows(handle, np.arange(64))
    counts = np.zeros((64, len(positions)), dtype=np.float32)
    counts[:, selected] = raw
    expression = torch.from_numpy(expression_from_counts(counts)).cuda()
    target = protocol["official_targets"][0]
    condition = normalized_features(features, [target]).expand(64, -1).cuda()
    model.cuda()
    measured = np.zeros(len(positions), dtype=bool)
    measured[selected] = True
    model.measurement_mask.copy_(torch.from_numpy(measured.astype(np.float32)).cuda())
    results = {"migration": migration, "control_file": str(control_path), "target": target, "checks": []}
    for unfreeze in [False, True]:
        set_trainable(model, unfreeze)
        optimizer = torch.optim.AdamW([parameter for parameter in model.parameters() if parameter.requires_grad], lr=1e-5)
        torch.cuda.reset_peak_memory_stats()
        start = time.monotonic()
        for step in range(3):
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast("cuda", dtype=torch.bfloat16):
                prediction = model({"ctrl_cell_emb": expression, "pert_emb": condition})
            mask = torch.from_numpy(measured).cuda()
            loss = model._compute_distribution_loss(prediction.float()[None, :, mask], expression[None, :, mask]).mean()
            if not torch.isfinite(loss):
                raise ValueError("Non-finite smoke loss")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 10, error_if_nonfinite=True)
            if any(p.grad is not None for n, p in model.named_parameters() if not unfreeze and n.startswith("transformer_backbone.")):
                raise ValueError("Frozen backbone unexpectedly received gradients")
            optimizer.step()
        torch.cuda.synchronize()
        check = {"unfreeze": unfreeze, "shape": list(prediction.shape), "loss": loss.item(),
                 "seconds_for_three_steps": time.monotonic()-start, "peak_gpu_bytes": torch.cuda.max_memory_allocated()}
        generated = integer_counts(prediction.detach().float().cpu().numpy()[:, selected], raw,
                                   np.ones(len(selected), dtype=bool), np.random.default_rng(42))
        if not np.array_equal(generated.sum(axis=1), raw.sum(axis=1)):
            raise ValueError("Count adapter changed library depths")
        check["counts_contract"] = "passed"
        results["checks"].append(check)
        print(json.dumps(check), flush=True)
        del optimizer
    (work / "audit/smoke.json").write_text(json.dumps(results, indent=2)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    main(args.work, args.root)
