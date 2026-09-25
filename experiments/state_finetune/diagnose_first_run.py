"""Read-only, bounded composition audit of the first run; no training or scoring.

Saved predictions use the exact original template RNG. The optional NTC probe
uses CPU FP32, so it is a new diagnostic, not a bitwise replay of GPU bf16 export.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np
import torch

from data import gene_names, h5_column, read_rows
from export import templates
from model import build_model, expression_from_counts, load_features, normalized_features


def proportions(counts):
    values = np.asarray(counts, dtype=np.float64)
    totals = values.sum(axis=1, keepdims=True)
    if (totals <= 0).any():
        raise ValueError("Empty cell in diagnostic sample")
    return values / totals


def composition_summary(predicted, control, supervised):
    predicted_mean, control_mean = predicted.mean(axis=0), control.mean(axis=0)
    fallback_before = float(control_mean[~supervised].sum())
    fallback_after = float(predicted_mean[~supervised].sum())
    return {
        "ntc_fallback_fraction": fallback_before,
        "prediction_fallback_fraction": fallback_after,
        "fallback_mass_ratio": fallback_after / fallback_before if fallback_before else None,
        "mean_profile_total_variation": float(np.abs(predicted_mean - control_mean).sum() / 2),
    }


def run(args):
    torch.set_num_threads(1)
    protocol = json.loads((args.work / "protocol.json").read_text())
    positions = {name: i for i, name in enumerate(protocol["genes"])}
    supported = np.load(args.work / "runs/unfrozen/supervised.npy")
    sources = {name: np.load(args.work / "prepared" / name / "measured.npy")
               for name in protocol["training_sources"]}
    contexts = [("H1", args.work / "h1-benchmark/h1_controls.h5ad")]
    contexts += [(name, args.work / "controls" / f"context_{name}.h5ad") for name in "ABC"]
    result = {
        "scope": "First 3 sorted targets per context, 400 saved cells each; no new official score",
        "seed": 42, "saved_predictions": [], "ntc_probe": [],
        "limitations": ["Small target sample, not the whole submission",
                         "Composition audit cannot apportion the official score loss",
                         "NTC CPU FP32 probe is not a GPU bf16 replay"],
    }
    probe_inputs = []
    for context, control_path in contexts:
        arms = ["frozen", "unfrozen"] if context == "H1" else ["unfrozen"]
        for arm in arms:
            filename = f"h1-{arm}-seed42.h5ad" if context == "H1" else "abc-unfrozen-seed42.h5ad"
            with h5py.File(args.root / "predictions" / filename) as saved, h5py.File(control_path) as controls:
                genes = list(gene_names(controls))
                if list(gene_names(saved)) != genes:
                    raise ValueError("Saved/control gene axes differ")
                axis = np.array([positions[name] for name in genes])
                measured = supported[axis]
                labels = h5_column(saved["obs"], "target_gene")
                selected_context = (h5_column(saved["obs"], "context") == context
                                    if context != "H1" else np.ones(len(labels), dtype=bool))
                targets = sorted(set(labels[selected_context]))[:3]
                effects, records = [], []
                for target in targets:
                    seed = int.from_bytes(hashlib.sha256(f"42:{context}:{target}".encode()).digest()[:8], "little")
                    rng = np.random.default_rng(seed)
                    selected = templates(controls, rng)[:400]
                    raw = read_rows(controls, selected)
                    indices = np.flatnonzero(selected_context & (labels == target))
                    if len(indices) != 400:
                        raise ValueError("Expected exactly 400 cells per condition")
                    prediction = read_rows(saved, indices)
                    # This would catch a wrong RNG/template mapping, not just bad shapes.
                    np.testing.assert_array_equal(prediction.sum(axis=1), raw.sum(axis=1))
                    p, q = proportions(prediction), proportions(raw)
                    records.append({"target": str(target), "cells": 400,
                                    "exact_template_depth_match": True,
                                    **composition_summary(p, q, measured)})
                    effects.append(p.mean(axis=0) - q.mean(axis=0))
                    if arm == "unfrozen" and target == targets[0]:
                        probe_inputs.append((context, axis, raw[:64]))
                cosines = []
                for i in range(len(effects)):
                    for j in range(i):
                        denominator = np.linalg.norm(effects[i]) * np.linalg.norm(effects[j])
                        cosines.append(float(effects[i] @ effects[j] / denominator) if denominator else None)
                result["saved_predictions"].append({
                    "context": context, "arm": arm, "records": records,
                    "pairwise_effect_cosines": cosines,
                    "prediction_file": filename,
                    "export_contract": json.loads(saved.attrs.get("vc2026_export_contract", "null")),
                })

    if args.probe_ntc:
        features = load_features(args.root / "assets/ESM2_pert_features.pt")
        model, _ = build_model(args.work / "upstream/state", args.root / "assets/parent/best.ckpt",
                               protocol["genes"], features, protocol["parent_targets"])
        checkpoint_path = args.work / "runs/unfrozen/best.pt"
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        if checkpoint["protocol"]["gene_axis_sha256"] != protocol["gene_axis_sha256"]:
            raise ValueError("Probe checkpoint gene axis mismatch")
        model.load_state_dict(checkpoint["state_dict"], strict=True)
        model.eval()
        result["ntc_probe_checkpoint_step"] = checkpoint["step"]
        with checkpoint_path.open("rb") as stream:
            result["ntc_probe_checkpoint_sha256"] = hashlib.file_digest(stream, "sha256").hexdigest()
        del checkpoint
        feature = normalized_features(features, ["non-targeting"]).expand(64, -1)
        del features
        for context, axis, raw in probe_inputs:
            counts = np.zeros((64, len(positions)), dtype=np.float32)
            counts[:, axis] = raw
            mask = torch.zeros(len(positions))
            mask[axis] = 1
            model.measurement_mask.copy_(mask)
            with torch.inference_mode():
                prediction = model({"ctrl_cell_emb": torch.from_numpy(expression_from_counts(counts)),
                                    "pert_emb": feature}).numpy()[:, axis]
            measured = supported[axis]
            baseline = proportions(raw)
            # Same expected weights as integer_counts; omit multinomial noise.
            weights = np.expm1(np.clip(prediction.astype(np.float64), 0, np.log1p(10000.0)))
            weights[:, ~measured] = 10000 * baseline[:, ~measured]
            factor = 10000 / weights.sum(axis=1)
            result["ntc_probe"].append({
                "context": context, "cells": 64, "precision": "CPU FP32",
                **composition_summary(proportions(weights), baseline, measured),
                "control_split_half_profile_total_variation": float(
                    np.abs(baseline[:32].mean(axis=0) - baseline[32:].mean(axis=0)).sum() / 2),
                "fallback_expected_multiplier_quantiles": np.quantile(factor, [0, .5, 1]).tolist(),
                "control_mass_on_source_panel": {
                    name: float(baseline[:, source_mask[axis]].sum(axis=1).mean())
                    for name, source_mask in sources.items()},
            })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.output),
                      "saved_conditions": sum(len(item["records"]) for item in result["saved_predictions"]),
                      "ntc_contexts": len(result["ntc_probe"])}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--probe-ntc", action="store_true")
    run(parser.parse_args())
