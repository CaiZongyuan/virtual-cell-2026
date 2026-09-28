"""Finish a bounded local comparison; no credentials, upload or hidden labels."""

import argparse
import fcntl
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from select_candidate import read_result


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def run(args):
    work = args.work.resolve()
    lock = (work / "campaign.lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    code = Path(__file__).resolve().parent
    training = str(args.previous / ".venv/bin/python")
    evaluation = str(args.previous / ".eval-venv/bin/python")
    env = os.environ.copy()
    env["PYTHONPATH"] = ":".join(str(code.parent / name) for name in ["reliability_transfer", "effect_calibration", "calibrated_transfer", "state_finetune"])
    children = []

    def stage(name, trial, seconds, memory, command, background=False):
        record = work / "status" / f"{name}.json"
        if record.exists():
            raise FileExistsError(f"Stage already recorded: {name}; explicit repair required")
        cmd = [evaluation, str(code.parent / "effect_calibration/stage.py"), "--work", str(work),
               "--name", name, "--trial", trial, "--revision", args.revision,
               "--timeout", str(seconds), "--memory-gb", str(memory), "--", *command]
        p = subprocess.Popen(cmd, env=env, start_new_session=True)
        children.append(p)
        if background:
            return p
        if p.wait() != 0:
            raise RuntimeError(f"Failed stage: {name}")

    def predict(arm, seed=42):
        stage(f"{arm}-export-{seed}", arm if seed == 42 else "confirmation", 1800, 8,
              [training, str(code / "predict.py"), "--work", str(work), "--previous", str(args.previous),
               "--arm", arm, "--seed", str(seed), "--revision", args.revision])

    def score(arm, seed=42, background=True):
        return stage(f"{arm}-score-{seed}", arm if seed == 42 else "confirmation", 10800, 12,
              [evaluation, str(code.parent / "calibrated_transfer/score_cached_inputs.py"), "score",
               str(work / "predictions" / f"{arm}-seed{seed}.h5ad"), "--data-dir", str(args.previous / "h1-benchmark"),
               "--gene-chunk", "512", "--de-threads", "8", "--output", str(work / "evaluation" / f"{arm}-seed{seed}")], background)

    try:
        # Preparation is a prerequisite, not a silently repeated stage.
        prep = json.loads((work / "status/source-statistics.json").read_text())
        if prep["exit_code"] != 0:
            raise RuntimeError("Source preparation did not complete successfully")
        baseline_manifest = json.loads((args.incumbent / "evaluation/control/manifest.json").read_text())
        incumbent = read_result(args.incumbent / "evaluation/empirical", baseline_manifest,
                                args.incumbent / "predictions/empirical.h5ad")
        control = read_result(args.incumbent / "evaluation/control", baseline_manifest)
        packages = {name: importlib.metadata.version(name) for name in ["cell-eval2", "pdex"]}
        if packages != {"cell-eval2": "0.16.0", "pdex": "0.3.0"}:
            raise ValueError("Evaluator package versions changed")
        save_json(work / "baseline.json", {"incumbent": incumbent, "control": control, "packages": packages})
        stage("fit", "preparation", 1800, 8, [training, str(code / "fit.py"), "--previous", str(args.previous),
                "--incumbent", str(args.incumbent), "--work", str(work)])
        for arm in ["expanded", "shrunk"]:
            predict(arm)
        first = score("expanded")
        neural = [training, str(code.parent / "effect_calibration/residual.py"), "--previous", str(args.previous),
                  "--campaign", str(work / "denoised-training"), "--work", str(work),
                  "--prior-strength", "0.5", "--revision", args.revision]
        # One scorer during training. Wait for it if memory is unexpectedly tight.
        available = next(int(line.split()[1])*1024 for line in Path("/proc/meminfo").read_text().splitlines() if line.startswith("MemAvailable:"))
        if available < 14e9 and first.wait() != 0:
            raise RuntimeError("Expanded scorer failed")
        stage("state-smoke", "state", 600, 8, [*neural, "--steps", "2", "--output-subdir", "state-smoke"])
        stage("state-train", "state", 2400, 8, [*neural, "--steps", "6000"])
        predict("state")
        second = score("shrunk")
        while first.poll() is None and second.poll() is None:
            time.sleep(5)
        for p in [first, second]:
            if p.poll() not in [None, 0]:
                raise RuntimeError("A scorer failed; preserve existing predictions and stage record")
        third = score("state")
        for p in [first, second, third]:
            if p.wait() != 0:
                raise RuntimeError("A scorer failed")
        results = {}
        for arm in ["expanded", "shrunk", "state"]:
            result = read_result(work / "evaluation" / f"{arm}-seed42", baseline_manifest,
                                  work / "predictions" / f"{arm}-seed42.h5ad")
            result["accepted"] = (result["score"] >= incumbent["score"] + .01
                                  and result["raw"]["MSE"] <= incumbent["raw"]["MSE"]
                                  and result["raw"]["NMAE"] <= 1.1 * incumbent["raw"]["NMAE"])
            results[arm] = result
        accepted = [a for a, r in results.items() if r["accepted"]]
        selected = max(accepted, key=lambda a: results[a]["score"]) if accepted else "incumbent"
        summary = {"selected": selected, "incumbent": incumbent, "control": control, "candidates": results,
                   "source_revision": args.revision, "official_upload_performed": False,
                   "confirmation": None, "local_release_passed": False}
        save_json(work / "selection.json", summary)
        if selected != "incumbent":
            predict(selected, 43)
            score(selected, 43, False)
            confirmation = read_result(work / "evaluation" / f"{selected}-seed43", baseline_manifest,
                                        work / "predictions" / f"{selected}-seed43.h5ad")
            summary["confirmation"] = confirmation
            summary["local_release_passed"] = (confirmation["score"] >= results[selected]["score"]-.01
                and confirmation["score"] >= incumbent["score"]+.01
                and confirmation["raw"]["MSE"] <= incumbent["raw"]["MSE"]
                and confirmation["raw"]["NMAE"] <= 1.1*incumbent["raw"]["NMAE"])
        save_json(work / "summary.json", summary)
        print(json.dumps({"complete": True, "selected": selected,
                          "scores": {a: r["score"] for a, r in results.items()},
                          "local_release_passed": summary["local_release_passed"]}), flush=True)
    finally:
        for p in children:
            if p.poll() is None:
                # Stage.py catches KeyboardInterrupt and reaps its own process group.
                os.killpg(p.pid, signal.SIGINT)
                try:
                    p.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid, signal.SIGKILL)
                    p.wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--incumbent", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, lambda signum, frame: (_ for _ in ()).throw(KeyboardInterrupt()))
    run(args)
