"""Local bounded supervisor: finish the authorized submission and close helpers."""

import argparse
import datetime
import fcntl
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time

from dotenv import dotenv_values


def run(args):
    root = Path(__file__).resolve().parents[2]
    local = root / "output/reliability-transfer-20260926"
    local.mkdir(exist_ok=True)
    lock = (local / "finish-submission.lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    work, previous = args.work, args.previous
    code = work / "code/experiments"
    pythonpath = ":".join(str(code / d) for d in ["reliability_transfer", "effect_calibration", "calibrated_transfer", "state_finetune"])
    bridge = None
    bridge_log = None
    log = (local / "finish-submission.log").open("a", buffering=1)

    def update(phase, **details):
        record = {"phase": phase, "checked_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), **details}
        (local / "finish-submission-status.json").write_text(json.dumps(record, indent=2)+"\n")
        print(json.dumps(record), flush=True)

    def remote(argv, *, capture=False, secret_input=None, timeout=60):
        command = shlex.join(["env", f"PYTHONPATH={pythonpath}", *map(str, argv)])
        return subprocess.run([sys.executable, str(root / "output/autoresearch/remote.py"), command],
            input=secret_input, text=True, stdout=subprocess.PIPE if capture else log,
            stderr=subprocess.PIPE if capture else log, timeout=timeout)

    def read(name):
        result = remote(["cat", work / name], capture=True)
        if result.returncode:
            raise RuntimeError(f"Remote record unavailable: {name}")
        return json.loads(result.stdout)

    def stage(name, seconds, memory, command):
        path = work / "status" / f"{name}.json"
        if remote(["test", "-f", path], capture=True).returncode == 0:
            if read(f"status/{name}.json")["exit_code"] != 0:
                raise RuntimeError(f"Recorded failed stage needs explicit repair: {name}")
            return
        update(name)
        result = remote([previous / ".eval-venv/bin/python", code / "effect_calibration/stage.py",
            "--work", work, "--name", name, "--trial", "final-submission", "--revision", args.revision,
            "--timeout", str(seconds), "--memory-gb", str(memory), "--", *command], timeout=seconds+90)
        if result.returncode:
            raise RuntimeError(f"Submission stage failed: {name}")

    try:
        update("waiting_for_final_confirmation")
        deadline = time.monotonic()+14400
        while remote(["test", "-f", work / "final-selection.exit"], capture=True).returncode:
            if time.monotonic() >= deadline:
                raise TimeoutError("Final confirmation did not finish within its budget")
            time.sleep(30)
        result = remote(["cat", work / "final-selection.exit"], capture=True)
        if result.stdout.strip() != "0":
            raise RuntimeError("Final selector failed; inspect its recorded log")
        decision = read("final-selection.json")
        if decision["selected"] == "incumbent":
            update("complete_existing_best_retained", entry_id="wwojQdFnxb0tiobhyPe3", no_new_submission=True)
            return
        if decision["local_release_passed"] is not True:
            raise ValueError("Highest-scoring candidate has not passed confirmation")
        stage("official-export", 3600, 12, [previous / ".venv/bin/python", code / "reliability_transfer/export_official.py",
              "--previous", previous, "--incumbent", args.incumbent, "--work", work, "--revision", args.revision])
        stage("official-prep", 5400, 26, [previous / ".submit-venv/bin/python", code / "effect_calibration/prepare_submission.py",
              "--previous", previous, "--work", work])
        # The existing supervisor owns and reaps its proxy/tunnel children.
        update("starting_owned_network_bridge")
        bridge_log = (local / "submission-network.log").open("w", buffering=1)
        bridge = subprocess.Popen([sys.executable, str(root / "output/effect-calibration-20260926/network_bridge.py")],
                                  stdout=bridge_log, stderr=bridge_log)
        ready_deadline = time.monotonic()+45
        while "Owned loopback bridge ready" not in (local / "submission-network.log").read_text():
            if bridge.poll() is not None or time.monotonic() >= ready_deadline:
                raise RuntimeError("Owned network bridge failed to become ready")
            time.sleep(1)
        config = dotenv_values(root / ".env")
        payload = json.dumps({"token": config["VCC_TOKEN"], "https_proxy": "http://127.0.0.1:18792"})+"\n"
        access = None
        for _ in range(3):
            result = remote([previous / ".submit-venv/bin/python", code / "effect_calibration/access.py",
                "--output", work / "audit/access-final.json"], secret_input=payload, timeout=60)
            if result.returncode == 0:
                access = read("audit/access-final.json")
                break
            time.sleep(5)
        if not access or not access["can_submit"] or access["limit_reached"]:
            raise RuntimeError("Live account eligibility or allowance does not permit this upload")
        update("uploading_verified_artifact", selected=decision["selected"])
        result = remote(["timeout", "7200", previous / ".submit-venv/bin/python",
            code / "effect_calibration/official_submission.py", "upload", "--work", work,
            "--revision", args.revision], secret_input=payload, timeout=7250)
        if result.returncode:
            raise RuntimeError("Upload did not exit successfully; retain its entry ID and private resume record")
        deadline = time.monotonic()+10800
        failures = 0
        while time.monotonic() < deadline:
            result = remote([previous / ".submit-venv/bin/python", code / "effect_calibration/official_submission.py",
                "status", "--work", work, "--revision", args.revision], secret_input=payload, timeout=60)
            if result.returncode not in [0, 2]:
                failures += 1
                if failures >= 3:
                    raise RuntimeError("Official status query failed repeatedly")
                time.sleep(30)
                continue
            failures = 0
            receipt = read("audit/official-submission.json")
            update("official_"+receipt["status"], **receipt)
            if receipt["status"] in ["published", "failed", "hidden_admin"]:
                return
            time.sleep(30)
        raise TimeoutError("Official scoring has not returned a terminal status within three hours")
    except BaseException as error:
        update("needs_review", error_type=type(error).__name__, reason=str(error))
        raise
    finally:
        if bridge is not None and bridge.poll() is None:
            bridge.terminate()
            try:
                bridge.wait(timeout=20)
            except subprocess.TimeoutExpired:
                bridge.kill()
                bridge.wait()
        if bridge_log is not None:
            bridge_log.close()
        log.close()
        (local / "finish-submission-cleanup.json").write_text(json.dumps({
            "checked_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "network_supervisor_stopped": bridge is None or bridge.poll() is not None,
            "scope": "Supervisor reaps its own proxy and SSH tunnel; final process audit follows."}, indent=2)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--incumbent", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    run(parser.parse_args())
