"""Finish this bounded local campaign after its already-running scores complete.

This controller has no credentials and never uploads. It stops at a fully
prepared artifact so the authorized upload can be separately observed/audited.
"""

import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time

from select_candidate import ARMS, require_stage


def run(args):
    work=args.work.resolve()
    lock=(work / "finish-local.lock").open("w")
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    code=Path(__file__).parent
    evaluation=str(args.previous / ".eval-venv/bin/python")
    training=str(args.previous / ".venv/bin/python")
    submission=str(args.previous / ".submit-venv/bin/python")
    environment=os.environ.copy()
    environment["PYTHONPATH"]=f"{code}:{code.parent}/calibrated_transfer:{code.parent}/state_finetune"

    def stage(name,trial,timeout,memory,command):
        try:
            status=require_stage(work,name)
        except FileNotFoundError:
            status=None
        if status is None:
            subprocess.run([evaluation,str(code / "stage.py"),"--work",str(work),"--name",name,
                "--trial",trial,"--revision",args.revision,"--timeout",str(timeout),
                "--memory-gb",str(memory),"--",*command],env=environment,check=True)
        else:
            print(json.dumps({"reused_completed_stage":status["stage"]}),flush=True)

    started=time.monotonic()
    last_report=0
    while True:
        pending=[]
        for arm,name in ARMS.items():
            if (work / "rejections" / f"{arm}.json").exists():
                continue
            try:
                require_stage(work,name)
            except FileNotFoundError:
                pending.append(arm)
        if not pending:
            break
        if time.monotonic()-started>10800:
            raise TimeoutError("Local score wait exceeded three hours")
        if time.monotonic()-last_report>60:
            print(json.dumps({"waiting_for_scores":pending}),flush=True)
            last_report=time.monotonic()
        time.sleep(10)
    if not (work / "selection.json").exists():
        subprocess.run([evaluation,str(code / "select_candidate.py"),"select","--work",str(work),
                        "--campaign",str(args.campaign)],env=environment,check=True)
    selected=json.loads((work / "selection.json").read_text())["selected_arm"]
    common=[training,str(code / "predict.py"),"--previous",str(args.previous),"--work",str(work),
            "--arm",selected,"--revision",args.revision]
    stage("confirmation-export","confirmation",1800,10,[*common,"--seed","43","--output",str(work / "predictions/confirmation.h5ad")])
    stage("confirmation-score","confirmation",10800,12,[evaluation,str(code.parent / "calibrated_transfer/score_cached_inputs.py"),
          "score",str(work / "predictions/confirmation.h5ad"),"--data-dir",str(args.previous / "h1-benchmark"),
          "--gene-chunk","512","--de-threads","8","--output",str(work / "evaluation/confirmation")])
    if not (work / "release.json").exists():
        subprocess.run([evaluation,str(code / "select_candidate.py"),"release","--work",str(work)],env=environment,check=True)
    if json.loads((work / "release.json").read_text())["released"] is not True:
        raise RuntimeError("Seed confirmation failed the frozen submission gate")
    stage("official-export","submission",3600,10,[*common,"--panel","abc","--seed","42","--output",str(work / "predictions/official.h5ad")])
    stage("official-prep","submission",5400,26,[submission,str(code / "prepare_submission.py"),"--previous",str(args.previous),"--work",str(work)])
    print(json.dumps({"local_campaign_complete":True,"selected_arm":selected,"official_artifact_prepared":True,"uploaded":False}),flush=True)


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--previous",type=Path,required=True)
    parser.add_argument("--campaign",type=Path,required=True)
    parser.add_argument("--work",type=Path,required=True)
    parser.add_argument("--revision",required=True)
    args=parser.parse_args()
    try:
        run(args)
    except Exception as error:
        (args.work / "finish-local-error.json").write_text(json.dumps({"type":type(error).__name__,"message":str(error),"time":time.time()},indent=2)+"\n")
        raise
