"""Regression: starting before the first run must not leave error 3500."""

import json
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request


def test_dashboard_waits_for_first_run_then_serves_experiments(tmp_path):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    logdir = tmp_path / "swanlog"
    server = subprocess.Popen([
        sys.executable, str(Path(__file__).with_name("dashboard.py")),
        "--logdir", str(logdir), "--port", str(port), "--wait-timeout", "30",
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        assert server.stdout.readline().startswith(b"Waiting for a recorded")
        with socket.socket() as sock:
            assert sock.connect_ex(("127.0.0.1", port)) != 0
        code = (
            "import swanlab,sys; "
            "swanlab.init(project='startup-regression',experiment_name='first-run',"
            "mode='local',logdir=sys.argv[1]); swanlab.log({'loss':1.0},step=1); swanlab.finish()"
        )
        subprocess.run([sys.executable, "-c", code, str(logdir)], check=True, capture_output=True, timeout=20)
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/v1/project", timeout=1) as response:
                    value = json.load(response)
                assert value["code"] == 0
                assert value["data"]["experiments"][0]["name"] == "first-run"
                break
            except (urllib.error.URLError, ConnectionError):
                time.sleep(0.1)
        else:
            raise AssertionError("Dashboard did not serve the first experiment")
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()
