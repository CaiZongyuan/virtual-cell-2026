"""Describe fixed H1 source-coverage strata without changing model selection."""

import argparse
import csv
import json
import math
from pathlib import Path


METRICS = {
    "pds_cosine": ("PDS", True),
    "expr_mse_unbiased": ("unscaled_unbiased_MSE", False),
    "de_wilcoxon_lfc_nmae": ("NMAE", False),
    "de_wilcoxon_direction_fidelity_yield_raw": ("FID", True),
    "de_wilcoxon_direction_reach_raw": ("REACH", True),
    "de_wilcoxon_sig_jaccard": ("JAC", True),
}


def read(folder):
    result = {}
    with (folder / "per_target.csv").open() as stream:
        for row in csv.DictReader(stream):
            if row["metric"] in METRICS:
                key = (row["target_gene"], row["metric"])
                value = float(row["value"])
                if key in result or not math.isfinite(value):
                    raise ValueError("Invalid or duplicate per-target value")
                result[key] = value
    return result


def run(args):
    definition = json.loads(args.groups.read_text())
    if not definition["before_any_candidate_scores"]:
        raise ValueError("Groups were not defined before candidate scores")
    baseline = read(args.baseline)
    results = {}
    for name in ["expanded", "shrunk", "state"]:
        candidate = read(args.work / "evaluation" / f"{name}-seed42")
        results[name] = {}
        for group, targets in definition["groups"].items():
            if not targets:
                continue
            results[name][group] = {"targets": len(targets), "metrics": {}}
            for metric, (label, maximize) in METRICS.items():
                old = [baseline[t, metric] for t in targets]
                new = [candidate[t, metric] for t in targets]
                delta = [n-o for n, o in zip(new, old)]
                results[name][group]["metrics"][label] = {
                    "incumbent_mean": sum(old)/len(old), "candidate_mean": sum(new)/len(new),
                    "paired_mean_change": sum(delta)/len(delta),
                    "targets_improved": sum(d > 0 if maximize else d < 0 for d in delta)}
    args.output.write_text(json.dumps({"group_definition": definition, "results": results,
        "scope": "Unweighted means over fixed H1 target strata, using original per-target raw values. Not official scaled scores or a new selection gate. Source coverage does not make H1 equivalent to official backgrounds."}, indent=2)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--groups", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args())
