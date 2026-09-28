"""Reuse an archived baseline only after validating the actual frozen assets."""

import argparse
import csv
import json
import math
from pathlib import Path
import shutil

from vcc_h1_eval import scorer
from vcc_h1_eval.artifacts import check
from vcc_h1_eval.paths import BenchmarkPaths


def reuse(previous, work, verify_only=False):
    origin = previous / "evaluation/control"
    manifest = json.loads((origin / "manifest.json").read_text())
    paths = BenchmarkPaths.resolve(previous / "h1-benchmark")
    check(paths)
    expected = {
        "packages": scorer.package_provenance(),
        "benchmark_manifest_sha256": scorer.sha256(paths.benchmark_manifest),
        "configuration_sha256": scorer.config_hash(scorer.public_config().to_dict()),
    }
    for key, value in expected.items():
        if manifest[key] != value:
            raise ValueError(f"Archived baseline differs: {key}")
    if manifest["controls"]["sha256"] != scorer.sha256(paths.controls):
        raise ValueError("Actual controls changed")
    if manifest["scale_bundle"]["manifest_sha256"] != scorer.sha256(paths.scale / "manifest.json"):
        raise ValueError("Scale bundle changed")
    if manifest["driver"]["gene_chunk"] != 512 or manifest["driver"]["de_threads"] != 8:
        raise ValueError("Archived driver differs from this campaign")
    generator = manifest["prediction"]
    if generator.get("seed_namespace") != scorer.CONTROL_BASELINE_SEED_NAMESPACE or generator.get("cells_per_target") != 400:
        raise ValueError("Archived baseline is not the canonical control generator")
    for item in manifest["outputs"].values():
        if scorer.sha256(origin / item["path"]) != item["sha256"]:
            raise ValueError("Archived score output checksum mismatch")
    with (origin / "scores.csv").open() as stream:
        scores = {r["metric"]: float(r["from_replicate"]) for r in csv.DictReader(stream)}
    if len(scores) != 7 or not all(math.isfinite(v) for v in scores.values()):
        raise ValueError("Archived baseline has incomplete/non-finite scores")
    receipt = {"origin": str(origin), "reused_measured_baseline": True,
               "score": scores["avg_score"], "benchmark_check_passed": True,
               "validation": "actual controls, scale, benchmark, config, installed evaluator packages and result hashes"}
    if not verify_only:
        attempts = work / "attempts.jsonl"
        if attempts.exists():
            raise FileExistsError("Use a fresh campaign directory; do not overwrite its ledger")
        output = work / "evaluation/control"
        output.mkdir(parents=True, exist_ok=True)
        for name in ["manifest.json", "scores.csv", "aggregates.csv", "per_target.csv"]:
            destination = output / name
            if destination.exists() and scorer.sha256(destination) != scorer.sha256(origin / name):
                raise ValueError(f"Different baseline already exists: {destination}")
            shutil.copy2(origin / name, destination)
        (work / "audit").mkdir(exist_ok=True)
        (work / "audit/baseline-reuse.json").write_text(json.dumps(receipt, indent=2)+"\n")
        attempts.write_text(json.dumps({"attempt": "control", "exit_code": None,
            "reused_measured_baseline": True, "origin": str(origin)})+"\n")
    print(json.dumps(receipt), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    reuse(args.previous, args.work, args.verify_only)
