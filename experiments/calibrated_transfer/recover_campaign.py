"""Recover immutable scoring artifacts after a connection interruption.

Run with the evaluation environment. This does not train or export predictions.
Existing complete scores are verified; incomplete scores resume upstream chunks.
"""

import argparse
import csv
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

from reuse_baseline import reuse
from summarize import METRICS, protocol_identity, summarize
from compare_targets import run as compare_targets


def active_scorers(work):
    active = []
    for process in Path("/proc").iterdir():
        if not process.name.isdigit():
            continue
        try:
            args = process.joinpath("cmdline").read_bytes().decode().split("\0")
        except (OSError, UnicodeError):
            continue
        if not args or Path(args[0]).name not in {"python", "python3", "vcc-h1"}:
            continue
        if any(str(work / "predictions" / f"{arm}.h5ad") in args for arm in ["empirical", "frozen", "limited"]):
            active.append(int(process.name))
    return active


def verify_complete(work, arm, baseline):
    from vcc_h1_eval.scorer import sha256

    folder = work / "evaluation" / arm
    required = ["manifest.json", "scores.csv", "aggregates.csv", "per_target.csv"]
    if not all((folder / name).exists() for name in required):
        return False
    manifest = json.loads((folder / "manifest.json").read_text())
    if protocol_identity(manifest) != protocol_identity(baseline):
        raise ValueError(f"Completed score uses a different protocol: {arm}")
    if manifest["controls"]["sha256"] != baseline["controls"]["sha256"]:
        raise ValueError("Completed score used different controls")
    if manifest["prediction"]["sha256"] != sha256(work / "predictions" / f"{arm}.h5ad"):
        raise ValueError(f"Prediction changed after scoring: {arm}")
    for item in manifest["outputs"].values():
        if sha256(folder / item["path"]) != item["sha256"]:
            raise ValueError(f"Score output checksum mismatch: {arm}")
    with (folder / "scores.csv").open() as stream:
        scores = {r["metric"]: float(r["from_replicate"]) for r in csv.DictReader(stream)}
    with (folder / "aggregates.csv").open() as stream:
        raw = {r["metric"]: float(r["raw_value"]) for r in csv.DictReader(stream) if r["metric"] in METRICS}
    if len(scores) != 7 or len(raw) != 6 or not all(math.isfinite(v) for v in [*scores.values(), *raw.values()]):
        raise ValueError("Incomplete/non-finite score artifacts")
    if not math.isclose(scores["avg_score"], sum(v for k,v in scores.items() if k != "avg_score")/6, abs_tol=1e-12):
        raise ValueError("Overall score differs from the six-metric mean")
    return True


def run(args):
    work = args.work.resolve()
    running = active_scorers(work)
    if running:
        raise RuntimeError(f"Existing scorers still run: {running}; do not launch duplicates")
    reuse(args.previous, work, verify_only=True)
    baseline = json.loads((work / "evaluation/control/manifest.json").read_text())
    previous_baseline = json.loads((args.previous / "evaluation/control/manifest.json").read_text())
    if baseline != previous_baseline:
        raise ValueError("Campaign baseline is not the verified archived baseline")
    records = [{"attempt":"control", "exit_code":None, "reused_measured_baseline":True,
                "origin":str(args.previous / "evaluation/control")}]
    env = os.environ.copy()
    env.update(OMP_NUM_THREADS="4", OPENBLAS_NUM_THREADS="4", MKL_NUM_THREADS="4",
               PYTHONPATH=f"{Path(__file__).parent}:{work}/code/experiments/state_finetune")
    for arm in ["empirical", "frozen", "limited"]:
        complete = verify_complete(work, arm, baseline)
        if not complete:
            memory = {line.split()[0].rstrip(":"): int(line.split()[1]) for line in Path("/proc/meminfo").read_text().splitlines()}
            if memory["MemAvailable"] * 1024 < 12_000_000_000:
                raise RuntimeError("Less than 12 GB RAM available for resident scoring")
            log = work / "logs" / f"{arm}-recovery-{int(time.time())}.log"
            command = ["timeout", "10800", sys.executable, str(Path(__file__).with_name("score_cached_inputs.py")),
                       "score", str(work / "predictions" / f"{arm}.h5ad"), "--data-dir", str(args.previous / "h1-benchmark"),
                       "--gene-chunk", "512", "--de-threads", "8", "--output", str(work / "evaluation" / arm)]
            with log.open("w") as stream:
                result = subprocess.run(command, env=env, stdout=stream, stderr=subprocess.STDOUT)
            if result.returncode != 0:
                raise RuntimeError(f"{arm} scoring failed ({result.returncode}); inspect {log}")
            if not verify_complete(work, arm, baseline):
                raise RuntimeError("Scoring did not produce complete validated artifacts")
        records.append({"attempt":arm, "exit_code":0, "action":"verify existing complete artifacts" if complete else "resume scoring",
                        "original_process_exit":"unknown after disconnect" if complete else 0,
                        "training_repeated":False, "verified_at_unix":time.time()})
    ledger = work / "attempts.jsonl"
    if ledger.exists():
        ledger.rename(work / "audit" / f"attempts-before-recovery-{time.time_ns()}.jsonl")
    ledger.write_text("".join(json.dumps(record)+"\n" for record in records))
    summary = summarize(work)
    (work / "summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    compare_targets(work)
    if args.confirm and summary["best"] != "control":
        if (work / "confirmation").exists():
            raise RuntimeError("Confirmation directory already exists: inspect it before any repeat")
        subprocess.run([str(args.previous / ".venv/bin/python"), str(Path(__file__).with_name("confirm.py")),
                        "--previous", str(args.previous), "--work", str(work), "--root", str(args.root),
                        "--arm", summary["best"]], env=env, check=True)
    print(json.dumps({"best":summary["best"], "score":summary["results"][summary["best"]]["metric"]}),flush=True)


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--previous",type=Path,required=True)
    parser.add_argument("--work",type=Path,required=True)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--confirm",action="store_true")
    run(parser.parse_args())
