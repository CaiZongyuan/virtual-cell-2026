"""Honor the user's final request: submit the highest valid score, then stop."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import time

from select_candidate import read_result, require_stage


def run(args):
    work = args.work.resolve()
    if not (work / "controller.exit").exists():
        raise ValueError("Wait for the existing campaign controller to finish")
    output = work / "final-selection.json"
    if output.exists():
        raise FileExistsError("Final selection already recorded")
    baseline = json.loads((args.incumbent / "evaluation/control/manifest.json").read_text())
    incumbent = read_result(args.incumbent / "evaluation/empirical", baseline,
                            args.incumbent / "predictions/empirical.h5ad")
    results = {"incumbent": incumbent}
    for arm in ["expanded", "shrunk", "state"]:
        status_path = work / "status" / f"{arm}-score-42.json"
        if not status_path.exists():
            raise ValueError(f"Candidate has no terminal scoring record: {arm}")
        status = json.loads(status_path.read_text())
        if status["exit_code"] != 0:
            results[arm] = {"status": "failed", "exit_code": status["exit_code"]}
            continue
        value = read_result(work / "evaluation" / f"{arm}-seed42", baseline,
                            work / "predictions" / f"{arm}-seed42.h5ad")
        value["original_improvement_gate_passed"] = (value["score"] >= incumbent["score"]+.01
            and value["raw"]["MSE"] <= incumbent["raw"]["MSE"]
            and value["raw"]["NMAE"] <= 1.1*incumbent["raw"]["NMAE"])
        results[arm] = value
    valid = [a for a, r in results.items() if r["status"] == "valid"]
    best = max(valid, key=lambda a: results[a]["score"])
    decision = {"requested_best": best, "selected": best, "results": results,
        "policy": "Highest valid H1 composite per the user's final instruction; original .01/MSE gates remain reported, not silently relabeled as passed.",
        "user_instruction": "本次训练结束之后，取最好成绩提交排行榜，然后停止工作",
        "source_revision": args.revision, "confirmation": None,
        "local_release_passed": False, "official_upload_performed": False}
    # Freeze the final user-directed ranking before inspecting a new seed.
    with (work / "final-selection-plan.json").open("x") as stream:
        json.dump({**decision, "frozen_at_unix": time.time()}, stream, indent=2)
        stream.write("\n")
    if best != "incumbent":
        code = Path(__file__).parent
        env = os.environ.copy()
        env["PYTHONPATH"] = ":".join(str(code.parent / d) for d in ["reliability_transfer", "effect_calibration", "calibrated_transfer", "state_finetune"])

        def stage(name, timeout, memory, command):
            subprocess.run([str(args.previous / ".eval-venv/bin/python"), str(code.parent / "effect_calibration/stage.py"),
                "--work", str(work), "--name", name, "--trial", "final-confirmation", "--revision", args.revision,
                "--timeout", str(timeout), "--memory-gb", str(memory), "--", *command], env=env, check=True)

        standard = work / "status" / f"{best}-score-43.json"
        if standard.exists():
            require_stage(work, f"{best}-score-43")
            decision["confirmation_reused"] = True
        else:
            if (work / "predictions" / f"{best}-seed43.h5ad").exists():
                raise ValueError("Interrupted confirmation requires explicit review")
            stage("final-confirmation-export", 1800, 8,
                [str(args.previous / ".venv/bin/python"), str(code / "predict.py"), "--previous", str(args.previous),
                 "--work", str(work), "--arm", best, "--seed", "43", "--revision", "4a4913ee2c10c058cb415ef4fc1d95d33d41d461"])
            stage("final-confirmation-score", 10800, 12,
                [str(args.previous / ".eval-venv/bin/python"), str(code.parent / "calibrated_transfer/score_cached_inputs.py"),
                 "score", str(work / "predictions" / f"{best}-seed43.h5ad"), "--data-dir", str(args.previous / "h1-benchmark"),
                 "--gene-chunk", "512", "--de-threads", "8", "--output", str(work / "evaluation" / f"{best}-seed43")])
            decision["confirmation_reused"] = False
        confirmation = read_result(work / "evaluation" / f"{best}-seed43", baseline,
                                   work / "predictions" / f"{best}-seed43.h5ad")
        decision["confirmation"] = confirmation
        decision["local_release_passed"] = (confirmation["score"] >= incumbent["score"]
                                             and confirmation["score"] >= results[best]["score"]-.01)
        if not decision["local_release_passed"]:
            decision["selected"] = "incumbent"
            decision["fallback_reason"] = "Highest first-seed candidate failed the final stability confirmation; retain the already published incumbent."
    decision["recorded_at_unix"] = time.time()
    output.write_text(json.dumps(decision, indent=2)+"\n")
    print(json.dumps({"selected": decision["selected"], "requested_best": best,
                      "first_scores": {a: r.get("score") for a, r in results.items()},
                      "local_release_passed": decision["local_release_passed"]}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--incumbent", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    run(parser.parse_args())
