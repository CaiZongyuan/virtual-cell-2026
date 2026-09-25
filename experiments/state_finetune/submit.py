"""Submit a validated artifact; receive credentials through stdin, never argv."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys


# User decision, 2026-09-25: run local evaluations until submissions are resumed.
OFFICIAL_SUBMISSIONS_ENABLED = False


def new_public_name():
    """Use an opaque public label; keep model provenance in the local manifest."""
    return f"entry-{secrets.token_hex(8)}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    args = parser.parse_args()
    if not OFFICIAL_SUBMISSIONS_ENABLED:
        raise SystemExit("Official submissions are paused by the user; use local evaluation.")
    model_name = new_public_name()
    prep = json.loads((args.work / "audit/submission-prep.json").read_text())
    if (prep.get("n_cells") != 360000 or prep.get("n_genes") != 18533
            or prep.get("dry_run") is not False or prep.get("verified_targets") is not True
            or prep.get("normalization") != "counts-preserved"
            or prep.get("cells_per_context") != {"A": 120000, "B": 120000, "C": 120000}
            or Path(prep["output"]).resolve() != args.artifact.resolve()):
        raise ValueError("Artifact does not match completed full submission preflight")
    from vcc.vccfile import validate_vcc
    validate_vcc(str(args.artifact))
    with args.artifact.open("rb") as stream:
        checksum = hashlib.file_digest(stream, "sha256").hexdigest()
    manifest = {"path": str(args.artifact), "bytes": args.artifact.stat().st_size,
                "sha256": checksum, "model_name": model_name, "preflight": prep}
    (args.work / "audit/submission-artifact.json").write_text(json.dumps(manifest, indent=2)+"\n")

    credentials = json.loads(sys.stdin.readline())
    token = credentials["token"]
    env = os.environ.copy()
    env["VCC_TOKEN"] = token
    if credentials.get("https_proxy"):
        env["HTTPS_PROXY"] = credentials["https_proxy"]
        env["HTTP_PROXY"] = credentials["https_proxy"]
    vcc = str(Path(sys.executable).with_name("vcc"))
    identity = subprocess.run([vcc, "--json", "whoami"], env=env, capture_output=True, text=True, timeout=60)
    if identity.returncode:
        raise RuntimeError((identity.stdout + identity.stderr).replace(token, "<REDACTED>"))
    status = json.loads(identity.stdout)
    if not status.get("identity", {}).get("can_submit"):
        raise RuntimeError("Submission account is not ready")
    print(json.dumps({"stage": "upload", "artifact_sha256": checksum, "model_name": model_name}), flush=True)
    process = subprocess.Popen([vcc, "--json", "submit", str(args.artifact),
                                "--model-name", model_name, "--wait"],
                               env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        print(line.rstrip("\n").replace(token, "<REDACTED>"), flush=True)
    raise SystemExit(process.wait())


if __name__ == "__main__":
    main()
