"""Rank only successful, finite scores under identical evaluator artifacts."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

METRICS = {
    "pds_cosine": "PDS", "expr_mse_unbiased_capped_norm": "MSE",
    "de_wilcoxon_lfc_nmae": "NMAE", "de_wilcoxon_direction_fidelity_yield_raw": "FID",
    "de_wilcoxon_direction_reach_raw": "REACH", "de_wilcoxon_sig_jaccard": "JAC",
    "avg_score": "avg_score",
}


def read_metrics(path, column):
    with path.open() as stream:
        return {METRICS[r["metric"]]: float(r[column]) for r in csv.DictReader(stream) if r["metric"] in METRICS}


def protocol_identity(manifest):
    return {k: manifest[k] for k in ["benchmark_manifest_sha256", "configuration_sha256", "driver", "packages", "scale_bundle"]}


def summarize(work):
    attempts = [json.loads(line) for line in (work / "attempts.jsonl").read_text().splitlines()]
    if len({r["attempt"] for r in attempts}) != len(attempts):
        raise ValueError("Duplicate attempts must be resolved explicitly")
    baseline_manifest = json.loads((work / "evaluation/control/manifest.json").read_text())
    results = {}
    for attempt in attempts:
        arm = attempt["attempt"]
        directory = work / "evaluation" / arm
        result = {**attempt, "status": "crash", "metric": None, "log": attempt.get("log", f"logs/{arm}.log")}
        if attempt["exit_code"] == 0 or attempt.get("reused_measured_baseline", False):
            scaled = read_metrics(directory / "scores.csv", "from_replicate")
            raw = read_metrics(directory / "aggregates.csv", "raw_value")
            if len(scaled) != 7 or len(raw) != 6 or not all(math.isfinite(x) for x in [*scaled.values(), *raw.values()]):
                raise ValueError(f"Missing/non-finite metrics for {arm}")
            manifest = json.loads((directory / "manifest.json").read_text())
            if protocol_identity(manifest) != protocol_identity(baseline_manifest):
                raise ValueError(f"Evaluator protocol differs for {arm}")
            for filename in ["scores", "aggregates", "per_target"]:
                data = (directory / f"{filename}.csv").read_bytes()
                if hashlib.sha256(data).hexdigest() != manifest["outputs"][filename]["sha256"]:
                    raise ValueError(f"Output checksum differs: {arm}/{filename}")
            result.update(status="valid", metric=scaled["avg_score"], scaled=scaled, raw=raw,
                          scores_sha256=manifest["outputs"]["scores"]["sha256"])
        results[arm] = result
    if results.get("control", {}).get("status") != "valid":
        raise ValueError("No valid measured baseline")
    control = results["control"]
    accepted = []
    for arm, result in results.items():
        if arm == "control" or result["status"] != "valid":
            continue
        result["delta_vs_control"] = result["metric"] - control["metric"]
        result["acceptance_gate_passed"] = result["delta_vs_control"] >= 0.01 and all(
            result["raw"][metric] < 2*control["raw"][metric] for metric in ["MSE", "NMAE"])
        if result["acceptance_gate_passed"]:
            accepted.append(arm)
    best = max(accepted, key=lambda arm:results[arm]["metric"]) if accepted else "control"
    for arm, result in results.items():
        if result["status"] == "valid":
            result["outcome"] = "keep" if arm == best else "discard"
    return {"development_panel": "H1 canonical 126x400, 18080 genes", "official_score": False,
            "best": best, "provisional_single_seed": best != "control", "results": results,
            "evaluator": protocol_identity(baseline_manifest)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("work", type=Path)
    args = parser.parse_args()
    result = summarize(args.work)
    (args.work / "summary.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({"best": result["best"], "scores": {k:v["metric"] for k,v in result["results"].items()}}))
