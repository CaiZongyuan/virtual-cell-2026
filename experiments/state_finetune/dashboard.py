"""Start SwanLab only after its project DB exists, on a fixed available port."""

import argparse
import os
from pathlib import Path
import socket
import sqlite3
import sys
import time


def project_ready(logdir):
    path = Path(logdir) / "runs.swanlab"
    if not path.exists():
        return False
    try:
        with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=1) as connection:
            return connection.execute("SELECT COUNT(*) FROM project").fetchone()[0] > 0
    except sqlite3.Error:
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--logdir", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=16906)
    parser.add_argument("--wait-timeout", type=float, default=300)
    args = parser.parse_args()
    deadline = time.monotonic() + args.wait_timeout
    print("Waiting for a recorded SwanLab project before starting the dashboard", flush=True)
    while not project_ready(args.logdir):
        if time.monotonic() >= deadline:
            raise SystemExit(f"No recorded SwanLab project found in {args.logdir}")
        time.sleep(0.2)
    with socket.socket() as probe:
        try:
            probe.bind((args.host, args.port))
        except OSError as error:
            raise SystemExit(f"Dashboard port {args.port} is unavailable; refusing an automatic port change: {error}")
    command = str(Path(sys.executable).with_name("swanlab"))
    os.execv(command, [command, "watch", str(args.logdir), "--host", args.host, "--port", str(args.port)])


if __name__ == "__main__":
    main()
