"""Run one bounded stage, retaining every exit status and interrupted log."""

import argparse
import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import time


def run(args):
    for folder in ["logs","status","attempts","trials"]:
        (args.work / folder).mkdir(parents=True,exist_ok=True)
    status = args.work / "status" / f"{args.name}.json"
    if status.exists():
        raise FileExistsError("Use a new stage name for a recorded retry")
    started = time.time()
    trial_path = args.work / "trials" / f"{args.trial}.json"
    if not trial_path.exists():
        with trial_path.open("x") as stream:
            json.dump({"trial":args.trial,"started_at_unix":started,"deadline_unix":started+14400},stream)
    deadline = json.loads(trial_path.read_text())["deadline_unix"]
    log = args.work / "logs" / f"{args.name}-{time.time_ns()}.log"
    record = {"stage":args.name,"trial":args.trial,"source_revision":args.revision,
              "started_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "command":args.command,"log":str(log.relative_to(args.work)),"exit_code":None}
    process = None
    try:
        roots = [p for p in Path.home().glob("vcc2026-*") if p.is_dir()]
        roots += [p for p in [Path("/mnt/e/vcc2026-data"),Path.home()/".cache/uv"] if p.exists()]
        used = sum(int(subprocess.check_output(["du","-sb",str(p)]).split()[0]) for p in roots)
        record["project_storage_bytes_before_stage"] = used
        if used > 450_000_000_000:
            raise RuntimeError("Less than 50 GB project storage headroom")
        available = next(int(line.split()[1])*1024 for line in Path("/proc/meminfo").read_text().splitlines() if line.startswith("MemAvailable:"))
        if available < args.memory_gb*1e9:
            raise RuntimeError("Insufficient available memory for this stage")
        timeout = min(args.timeout,deadline-started)
        if timeout <= 0:
            raise RuntimeError("Trial's four-hour deadline is exhausted")
        record["timeout_seconds"] = timeout
        env = os.environ.copy()
        env.update(OMP_NUM_THREADS="4",OPENBLAS_NUM_THREADS="4",MKL_NUM_THREADS="4",PYTHONUNBUFFERED="1")
        with log.open("w") as stream:
            process = subprocess.Popen(args.command,stdout=stream,stderr=subprocess.STDOUT,env=env,start_new_session=True)
            try:
                record["exit_code"] = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGKILL)
                    process.wait()
                record.update(exit_code=124,error="stage or whole-trial timeout")
    except BaseException as error:
        if process is not None and process.poll() is None:
            os.killpg(process.pid,signal.SIGKILL)
            process.wait()
        record.update(exit_code=1,error=f"{type(error).__name__}: {error}")
    finally:
        record.update(elapsed_seconds=time.time()-started,finished_at_unix=time.time())
        text=json.dumps(record,indent=2)+"\n"
        (args.work / "attempts" / f"{args.name}-{time.time_ns()}.json").write_text(text)
        status.write_text(text)
    print(json.dumps(record),flush=True)
    raise SystemExit(record["exit_code"])


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--work",type=Path,required=True)
    parser.add_argument("--name",required=True)
    parser.add_argument("--trial",required=True)
    parser.add_argument("--revision",required=True)
    parser.add_argument("--timeout",type=int,required=True)
    parser.add_argument("--memory-gb",type=float,default=12)
    parser.add_argument("command",nargs=argparse.REMAINDER)
    args=parser.parse_args()
    if args.command and args.command[0]=="--":
        args.command=args.command[1:]
    if not args.command:
        parser.error("A command is required")
    run(args)
