"""One-shot Jurkat confirmation after selecting an arm on H1 development scores.

This measures normalized mean-expression error on Jurkat's measured gene panel.
It is NOT a reproduction of the six-metric H1 benchmark or its reference scaling.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

import numpy as np
import torch

from campaign import context_average, contrast, load_state, save_json, sha
from data import PreparedSource, prepare
from effects import cp10k, transfer_counts
from model import expression_from_counts, normalized_features


def run(args):
    # Freeze a named arm and its artifact hash BEFORE opening confirmation labels.
    out = args.work / "confirmation"
    out.mkdir(exist_ok=False)
    checkpoint = args.work / "runs" / args.arm / "final.pt"
    save_json(out / "selection.json", {
        "arm": args.arm,
        "effect_sha256": sha(args.work / "effects.npz"),
        "checkpoint_sha256": sha(checkpoint) if args.arm != "empirical" else None,
        "metric": "ratio of summed squared normalized-mean errors to sampled NTC",
        "seed": 991, "max_cells_per_target": 256, "target_self_excluded": True,
        "eligible_targets": "Jurkat conditions admitted by frozen prepared-source protocol and present in the external training effect table",
        "use": "one-shot confirmation; no tuning or retraining after result",
    })
    shutil.copy2(args.previous / "protocol.json", out / "protocol.json")
    prepare(args.root, out, "jurkat")
    source = PreparedSource(out / "prepared/jurkat")
    protocol = json.loads((out / "protocol.json").read_text())
    positions = {g: i for i, g in enumerate(protocol["genes"])}
    with np.load(args.work / "effects.npz") as archive:
        tables = {k: archive[k] for k in archive.files}
    entries = json.loads((args.work / "effects.json").read_text())["entries"]
    supported = {r["target"] for r in entries}
    groups = sorted([g for g in source.groups if g["target"] in supported], key=lambda g:g["target"])
    model = None
    if args.arm != "empirical":
        torch.set_num_threads(4)
        model, features, _, _ = load_state(args)
        state = torch.load(checkpoint, weights_only=False, map_location="cpu")
        model.load_state_dict(state["state_dict"], strict=True)
        del state
        model.measurement_mask.copy_(torch.from_numpy(source.measured.astype(np.float32)).cuda())
    rng = np.random.default_rng(991)
    results = []
    with torch.inference_mode():
        for group in groups:
            target = group["target"]
            # Preparation already capped each condition at 256 without replacement.
            rows = np.array(sorted(group["training"] + group["development"]))
            treated = source.counts[rows].toarray()
            control_rows = [int(rng.choice(source.controls_by_batch[str(b)])) for b in source.row_batches[rows]]
            control = source.counts[control_rows].toarray()
            if model is None:
                indices = [i for i, r in enumerate(entries) if r["target"] == target]
                delta, measured = context_average(tables["deltas"][indices], tables["masks"][indices],
                                                   [entries[i]["context"] for i in indices])
            else:
                extra = (-len(control)) % 64
                padded = np.concatenate([control, control[:extra]]) if extra else control
                x = torch.from_numpy(expression_from_counts(padded)).cuda().reshape(-1, 64, len(positions))
                vectors = normalized_features(features, [target]).cuda().expand(len(x), -1)
                with torch.autocast("cuda", dtype=torch.bfloat16):
                    delta = contrast(model, x, vectors).mean(0).cpu().numpy()
                measured = tables["masks"].any(0)
            prediction = transfer_counts(control, delta, measured & source.measured, rng)
            valid = source.measured.copy()
            if target in positions:
                valid[positions[target]] = False
            truth = cp10k(treated).mean(0)[valid]
            null = cp10k(control).mean(0)[valid]
            estimate = cp10k(prediction).mean(0)[valid]
            base_sse = float(np.square(null-truth).sum())
            candidate_sse = float(np.square(estimate-truth).sum())
            results.append({"target": target, "cells": len(rows), "baseline_sse": base_sse,
                            "candidate_sse": candidate_sse, "ratio": candidate_sse/base_sse if base_sse else None})
    ratios = [r["ratio"] for r in results if r["ratio"] is not None]
    summary = {"arm": args.arm, "targets": len(results), "cells": sum(r["cells"] for r in results),
               "baseline": 1.0,
               "pooled_error_ratio": sum(r["candidate_sse"] for r in results)/sum(r["baseline_sse"] for r in results),
               "median_target_ratio": float(np.median(ratios)), "targets_improved": sum(r < 1 for r in ratios),
               "metric_scope": "Jurkat normalized mean-expression error; not H1 canonical six-metric score",
               "details": results}
    save_json(out / "summary.json", summary)
    print(json.dumps({k:v for k,v in summary.items() if k!="details"}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("/mnt/e/vcc2026-data"))
    parser.add_argument("--arm", choices=["empirical", "frozen", "limited"], required=True)
    run(parser.parse_args())
