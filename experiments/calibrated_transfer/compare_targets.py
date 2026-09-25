"""Describe per-target wins and prepared-supervision coverage after scoring."""

import argparse
import csv
import json
import math
from pathlib import Path

from summarize import METRICS

PER_TARGET_METRICS = {**METRICS, "expr_mse_unbiased": "MSE_uncapped"}


def read(path):
    values = {}
    with path.open() as stream:
        for row in csv.DictReader(stream):
            if row["metric"] not in PER_TARGET_METRICS or not row["value"]:
                continue
            key = (row["target_gene"], PER_TARGET_METRICS[row["metric"]])
            if key in values:
                raise ValueError("Duplicate per-target metric")
            value = float(row["value"])
            if math.isfinite(value):
                values[key] = value
    return values


def run(work):
    summary = json.loads((work / "summary.json").read_text())
    coverage = json.loads((work / "audit/target-coverage.json").read_text())
    missing = set(coverage["h1_canonical_uncovered"])
    baseline = read(work / "evaluation/control/per_target.csv")
    report = {"scope": "paired raw per-target differences; MSE_uncapped is the uncapped audit metric, not the panel-normalized scored MSE; no significance tests",
              "coverage_scope": "supervision in the prepared campaign data, not the full pretraining history",
              "models": {}}
    for arm, outcome in summary["results"].items():
        if arm == "control" or outcome["status"] != "valid":
            continue
        candidate = read(work / "evaluation" / arm / "per_target.csv")
        groups = {}
        for group in ["all", "prepared_supervision", "no_prepared_supervision"]:
            metrics = {}
            for metric in ["PDS", "MSE_uncapped", "NMAE", "FID", "REACH", "JAC"]:
                pairs = [(t, candidate[(t,m)], v) for (t,m), v in baseline.items()
                         if m == metric and (t,m) in candidate
                         and (group == "all" or ((t in missing) == (group == "no_prepared_supervision")))]
                if not pairs:
                    continue
                direction = -1 if metric in {"MSE_uncapped", "NMAE"} else 1
                improved = [t for t,c,b in pairs if direction*(c-b)>1e-12]
                metrics[metric] = {"valid_targets":len(pairs), "improved_targets":len(improved),
                                   "baseline_raw_mean":sum(b for _,_,b in pairs)/len(pairs),
                                   "candidate_raw_mean":sum(c for _,c,_ in pairs)/len(pairs)}
            groups[group] = metrics
        report["models"][arm] = groups
    (work / "target-comparison.json").write_text(json.dumps(report,indent=2)+"\n")
    return report


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("work",type=Path)
    args=parser.parse_args()
    run(args.work)
