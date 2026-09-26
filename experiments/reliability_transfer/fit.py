"""Fit source-only noise priors and export frozen effect/State supervision tables."""

import argparse
import json
from pathlib import Path

import numpy as np

from campaign import SOURCES, CONTEXTS, save_json, sha
from effects import context_average, matched_means
from data import PreparedSource
from calibration import expected_mean
from shrinkage import fit_prior, posterior_mean


def aggregate(target, entries, values, masks, exclude=None):
    ids = [i for i, r in enumerate(entries) if r["target"] == target and r["context"] != exclude]
    if not ids:
        return np.zeros(values.shape[1]), np.zeros(values.shape[1], bool)
    return context_average(values[ids], masks[ids], [entries[i]["context"] for i in ids])


def run(args):
    if (args.work / "fit.json").exists():
        raise FileExistsError("Fitted campaign is immutable")
    protocol = json.loads((args.previous / "protocol.json").read_text())
    width = len(protocol["genes"])
    entries, expanded, shrunk, masks, controls = [], [], [], [], []
    priors, diagnostics = {}, {}
    for source in SOURCES:
        folder = args.work / "sources" / source
        meta = json.loads((folder / "summary.json").read_text())
        if sha(folder / "statistics.npz") != meta["statistics_sha256"]:
            raise ValueError("Source statistics changed")
        with np.load(folder / "statistics.npz") as table:
            effect, variance, control = [table[k] for k in ["effects", "variances", "controls"]]
            # Fit the prior where the delta-method approximation is less fragile.
            usable = control > .1
            weights, report = fit_prior(effect[usable], variance[usable])
            posterior = posterior_mean(effect, variance, weights)
            priors[source] = report
            diagnostics[source] = {"raw_effect_rms": float(np.sqrt(np.mean(effect**2))),
                                   "posterior_effect_rms": float(np.sqrt(np.mean(posterior**2)))}
            for i, target in enumerate(meta["targets"]):
                values = []
                for small in [effect[i], posterior[i], control[i]]:
                    full = np.zeros(width, np.float32)
                    full[table["gene_positions"]] = small
                    values.append(full)
                measured = np.zeros(width, bool)
                measured[table["gene_positions"]] = True
                expanded.append(values[0]); shrunk.append(values[1]); controls.append(values[2]); masks.append(measured)
                entries.append({"source": source, "context": CONTEXTS[source], "target": target, "cells": int(table["cells"][i])})
        print(json.dumps({"prior": source, **diagnostics[source], "weights": report["weights"]}), flush=True)
    expanded, shrunk, controls, masks = map(np.stack, [expanded, shrunk, controls, masks])
    targets = sorted({e["target"] for e in entries})
    for arm, values in [("expanded", expanded), ("shrunk", shrunk)]:
        combined = [aggregate(t, entries, values, masks) for t in targets]
        np.savez(args.work / f"{arm}.npz", deltas=np.stack([v[0] for v in combined]), masks=np.stack([v[1] for v in combined]))
    save_json(args.work / "effects.json", {"targets": targets, "entries": entries,
        "protocol_sha256": sha(args.previous / "protocol.json"),
        "candidate_hashes": {a: sha(args.work / f"{a}.npz") for a in ["expanded", "shrunk"]}})
    allowed = set()
    for source in SOURCES:
        m = json.loads((args.previous / "prepared" / source / "manifest.json").read_text())
        allowed.update((source, g["target"]) for g in m["groups"])
    ids = [i for i, e in enumerate(entries) if (e["source"], e["target"]) in allowed]
    neural = args.work / "denoised-training"
    neural.mkdir(exist_ok=False)
    np.savez(neural / "effects.npz", deltas=shrunk[ids], controls=controls[ids], masks=masks[ids])
    save_json(neural / "effects.json", {"entries": [entries[i] for i in ids], "sources": SOURCES,
        "protocol_sha256": sha(args.previous / "protocol.json")})
    old_meta = json.loads((args.incumbent / "effects.json").read_text())
    with np.load(args.incumbent / "effects.npz") as archive:
        old = {k: archive[k] for k in archive.files}
    records = []
    positions = {g: i for i, g in enumerate(protocol["genes"])}
    for name in SOURCES:
        source = PreparedSource(args.previous / "prepared" / name)
        for group in source.groups:
            target, context = group["target"], CONTEXTS[name]
            baseline_effect, baseline_mask = aggregate(target, old_meta["entries"], old["deltas"], old["masks"], context)
            if not baseline_mask.any():
                continue
            control, truth = matched_means(source, group, "development")
            valid = source.measured.copy()
            if target in positions:
                valid[positions[target]] = False
            errors = {"NTC": float(np.square(control[valid]-truth[valid]).sum())}
            for arm, values in [("incumbent", None), ("expanded", expanded), ("shrunk", shrunk)]:
                effect, mask = (baseline_effect, baseline_mask) if arm == "incumbent" else aggregate(target, entries, values, masks, context)
                prediction = expected_mean(control, effect, mask & source.measured, .5, "multiplicative")
                errors[arm] = float(np.square(prediction[valid]-truth[valid]).sum())
            records.append({"source": name, "context": context, "target": target, "errors": errors})
        del source
    context_errors = {}
    for context in sorted(set(CONTEXTS.values())):
        rows = [r for r in records if r["context"] == context]
        denominator = sum(r["errors"]["NTC"] for r in rows)
        context_errors[context] = {a: sum(r["errors"][a] for r in rows)/denominator for a in ["incumbent", "expanded", "shrunk"]}
    report = {"source_priors": priors, "source_diagnostics": diagnostics,
              "entries": len(entries), "targets": len(targets), "training_cells": sum(e["cells"] for e in entries),
              "neural_conditions": len(ids), "source_context_error_ratios": context_errors,
              "source_context_equal_mean": {a: float(np.mean([v[a] for v in context_errors.values()])) for a in ["incumbent", "expanded", "shrunk"]},
              "scope": "Source biological-context exclusion on old held development cells; moment surrogate, not H1 score. Both K562 sources excluded together. Independent of H1 and Jurkat response labels.",
              "records": records}
    save_json(args.work / "fit.json", report)
    print(json.dumps({k: v for k, v in report.items() if k not in ["records", "source_priors"]}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--incumbent", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    run(parser.parse_args())
