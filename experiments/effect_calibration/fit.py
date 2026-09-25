"""Fit empirical strengths without reading H1 or Jurkat perturbation labels."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from calibration import GRID, additive_effects, aggregate, expected_mean
from campaign import SOURCES, CONTEXTS, save_json, sha
from data import PreparedSource
from effects import matched_means


def run(args):
    args.work.mkdir(parents=True, exist_ok=True)
    if (args.work / "fit.json").exists():
        raise FileExistsError("Source fitting already completed; inspect the fixed result")
    with np.load(args.campaign / "effects.npz") as archive:
        tables = {k: archive[k] for k in archive.files}
    entries = json.loads((args.campaign / "effects.json").read_text())["entries"]
    shifts = additive_effects(tables["deltas"], tables["controls"], tables["masks"])
    protocol = json.loads((args.previous / "protocol.json").read_text())
    positions = {g: i for i,g in enumerate(protocol["genes"])}
    targets = sorted({r["target"] for r in entries})
    log_deltas, mean_shifts, masks = [], [], []
    for target in targets:
        log, mask = aggregate(target, entries, tables["deltas"], tables["masks"])
        shift, additive_mask = aggregate(target, entries, shifts, tables["masks"])
        assert np.array_equal(mask, additive_mask)
        log_deltas.append(log)
        mean_shifts.append(shift)
        masks.append(mask)
    np.savez(args.work / "effects.npz", log_deltas=np.asarray(log_deltas, np.float64),
             mean_shifts=np.asarray(mean_shifts, np.float64), masks=np.stack(masks))
    save_json(args.work / "effects.json", {"targets": targets,
              "source_effects_sha256": sha(args.campaign / "effects.npz"),
              "source_entries_sha256": sha(args.campaign / "effects.json"),
              "protocol_sha256": sha(args.previous / "protocol.json")})
    records = []
    for source_name in SOURCES:
        context = CONTEXTS[source_name]
        source = PreparedSource(args.previous / "prepared" / source_name)
        for group in source.groups:
            target = group["target"]
            log, mask = aggregate(target, entries, tables["deltas"], tables["masks"], context)
            mask &= source.measured
            if not mask.any():
                continue
            shift, _ = aggregate(target, entries, shifts, tables["masks"], context)
            control, truth = matched_means(source, group, split="development")
            valid = source.measured.copy()
            if target in positions:
                valid[positions[target]] = False
            baseline = float(np.square(control[valid]-truth[valid]).sum())
            values = {}
            for mode, delta in [("multiplicative", log), ("additive", shift)]:
                values[mode] = [float(np.square(expected_mean(control,delta,mask,alpha,mode)[valid]-truth[valid]).sum()) for alpha in GRID]
            records.append({"source":source_name,"context":context,"target":target,
                            "development_cells":len(group["development"]),"baseline_sse":baseline,"candidate_sse":values})
        print(json.dumps({"source":source_name,"calibration_conditions":sum(r["source"]==source_name for r in records)}),flush=True)
        del source
    contexts = sorted({r["context"] for r in records})
    if len(contexts) != 3:
        raise ValueError("Expected three calibration contexts")
    curves = {}
    for mode in ["multiplicative", "additive"]:
        curves[mode] = []
        for i, alpha in enumerate(GRID):
            ratios = {}
            for context in contexts:
                rows = [r for r in records if r["context"] == context]
                ratios[context] = sum(r["candidate_sse"][mode][i] for r in rows)/sum(r["baseline_sse"] for r in rows)
            curves[mode].append({"alpha":alpha,"mean_context_ratio":float(np.mean(list(ratios.values()))),"context_ratios":ratios})
    selected = min(curves["additive"], key=lambda row:(row["mean_context_ratio"],row["alpha"]))
    save_json(args.work / "fit.json", {"scope":"empirical source-context exclusion using other contexts' training effects and held-context development cells; mean surrogate, not canonical score",
              "source_effects_sha256":sha(args.campaign / "effects.npz"),
              "prepared_manifests":{s:sha(args.previous / "prepared" / s / "manifest.json") for s in SOURCES},
              "grid":GRID,"curves":curves,"additive_strength":selected["alpha"],
              "conservative_strength":0.2,"calibration_conditions":len(records),
              "unique_targets":len({r["target"] for r in records}),"records":records})
    print(json.dumps({"additive_strength":selected["alpha"],"source_error_ratio":selected["mean_context_ratio"]}),flush=True)


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--previous",type=Path,required=True)
    parser.add_argument("--campaign",type=Path,required=True)
    parser.add_argument("--work",type=Path,required=True)
    run(parser.parse_args())
