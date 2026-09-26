"""Submit one released artifact; persist its ID before upload and resume safely."""

import argparse
import datetime
import json
import math
import os
from pathlib import Path
import re
import secrets
import sys
import time

from access import credentials, check
from prepare_submission import sha


ENDPOINT="https://virtualcellchallenge.org"


def write_json(path,value,private=False):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+".tmp")
    with temporary.open("w") as stream:
        if private:
            os.fchmod(stream.fileno(),0o600)
        json.dump(value,stream,indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def safe_scores(value,key=None):
    if isinstance(value,bool):
        return None
    if isinstance(value,(int,float)):
        return value if math.isfinite(value) else None
    if isinstance(value,dict):
        result={}
        for k,v in value.items():
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_ -]{0,100}",str(k)):
                continue
            item=safe_scores(v,str(k))
            if item is not None:
                result[k]=item
        return result
    if isinstance(value,list):
        return [item for v in value if (item:=safe_scores(v)) is not None]
    if isinstance(value,str):
        if key in {"metric","context","aggregation"} and re.fullmatch(r"[A-Za-z][A-Za-z0-9_ -]{0,100}",value):
            return value
        try:
            number=float(value)
        except ValueError:
            return None
        return number if math.isfinite(number) else None
    return None


def safe_status(entry):
    result={}
    for key in ["entry_id","id","status","model_name","created_at","updated_at","scored_at"]:
        value=entry.get(key)
        if isinstance(value,str) and len(value)<=200 and "://" not in value:
            result[key]=value
    if isinstance(entry.get("is_final"),bool):
        result["is_final"]=entry["is_final"]
    for key in ["score","overall_score","total_score","avg_score","scores","metrics"]:
        if key in entry:
            result[key]=safe_scores(entry[key])
    return result


def run(args):
    from vcc import api, submit
    from vcc.vccfile import validate_vcc

    work=args.work.resolve()
    release=json.loads((work / "release.json").read_text())
    preparation=json.loads((work / "audit/submission-preparation.json").read_text())
    if release["released"] is not True or preparation["release_sha256"]!=sha(work / "release.json"):
        raise ValueError("Submission release is missing or changed")
    artifact=Path(preparation["artifact_path"])
    if not preparation["native_prep_completed"] or preparation["matrix_count_values_changed"]:
        raise ValueError("Full native preparation has not completed with preserved counts")
    receipt_path=work / "audit/official-submission.json"
    receipt=json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
    plan_path=work / "audit/official-plan.json"
    if plan_path.exists():
        plan=json.loads(plan_path.read_text())
        if plan["artifact_sha256"]!=preparation["artifact_sha256"]:
            raise ValueError("Prepared artifact differs from the existing submission plan")
    elif args.action=="upload":
        plan={"model_name":f"entry-{secrets.token_hex(8)}","selected_arm":release["selected_arm"],
              "artifact_sha256":preparation["artifact_sha256"],"artifact_bytes":preparation["artifact_bytes"],
              "release_sha256":sha(work / "release.json"),"effects_sha256":release["effects_sha256"],
              "fit_sha256":release["fit_sha256"],"checkpoint_sha256":release["checkpoint_sha256"],
              "created_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "source_revision":args.revision,"submission_count_limit":1}
        write_json(plan_path,plan)
    else:
        raise ValueError("No existing submission plan")
    token=credentials()
    private=work / "private"
    private.mkdir(mode=0o700,exist_ok=True)
    private.chmod(0o700)
    pending_path=private / "pending-uploads.json"
    pending=json.loads(pending_path.read_text()) if pending_path.exists() else {}

    def status():
        if not receipt.get("entry_id"):
            raise ValueError("No durable entry ID; do not create another entry blindly")
        entry=api.get_submission(ENDPOINT,token,receipt["entry_id"])
        if entry.get("status") not in {"uploading","launching","pending","scoring","published","failed","hidden_admin"}:
            raise ValueError("Unknown submission status; preserve the existing entry")
        receipt.update(safe_status(entry),checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        write_json(receipt_path,receipt)
        print(json.dumps(receipt),flush=True)
        return entry

    if args.action=="status":
        entry=status()
        return 0 if entry.get("status") not in {"failed","hidden_admin"} else 2
    if receipt.get("entry_id"):
        entry=status()
        if entry.get("status")!="uploading":
            # Launch may already have succeeded despite a lost HTTP response.
            return 0 if entry.get("status") not in {"failed","hidden_admin"} else 2
        if receipt["entry_id"] not in pending:
            raise ValueError("Existing upload has no private resume record; do not create another")
    elif receipt.get("creation_attempted"):
        raise ValueError("An earlier create call was ambiguous; resolve its entry ID before retrying")
    if sha(artifact)!=plan["artifact_sha256"]:
        raise ValueError("Packed artifact changed after its audited preparation")
    validate_vcc(str(artifact))
    access=check(token)
    write_json(work / "audit/access-before-upload.json",access)
    if not access["can_submit"] or (access["limit_reached"] and not receipt.get("entry_id")):
        raise ValueError("Live account eligibility or daily allowance disallows this new upload")

    def save_resume(entry_id,record):
        pending[entry_id]=record
        write_json(pending_path,pending,private=True)

    def clear_resume(entry_id):
        pending.pop(entry_id,None)
        write_json(pending_path,pending,private=True)

    last_progress=0.0

    def on_event(kind,**data):
        nonlocal last_progress
        public={"event":kind,"at_unix":time.time()}
        if kind=="create_start":
            receipt.update(creation_attempted=True,model_name=plan["model_name"],artifact_sha256=plan["artifact_sha256"])
        if kind=="created":
            receipt.update(entry_id=data["entry_id"],is_final=data["is_final"],status="uploading")
            public.update(entry_id=data["entry_id"],is_final=data["is_final"])
        elif kind=="launched":
            receipt.update(entry_id=data["entry_id"],status="launching")
            public["entry_id"]=data["entry_id"]
        elif kind=="upload_done":
            receipt.update(bytes_uploaded=data["bytes"],md5_verified=data["verified"])
            public.update(bytes_uploaded=data["bytes"],md5_verified=data["verified"])
        elif kind=="upload_progress":
            if time.monotonic()-last_progress<30:
                return
            last_progress=time.monotonic()
            public.update(done=data["done"],total=data["total"])
        elif kind not in {"create_start","upload_start","resume","limit_check"}:
            return
        write_json(receipt_path,receipt)
        with (work / "audit/official-events.jsonl").open("a") as stream:
            stream.write(json.dumps(public)+"\n")
        print(json.dumps(public),flush=True)
        if kind=="created" and data["is_final"]:
            raise ValueError("This campaign authorizes the validation round, not a final entry")

    result=submit.run_submit(endpoint=ENDPOINT,token=token,path=str(artifact),model_name=plan["model_name"],
        description="External CRISPRi data: Replogle et al. and Nadig/O'Conner et al., via scPerturb (Zenodo 13350497, CC BY 4.0). Fixed fitted predictor and raw-count generation; complete provenance archived with the method.",
        wait=False,on_event=on_event,skip_limit_check=False,
        resume=pending.get(receipt.get("entry_id")),pending_uploads=pending,
        save_resume=save_resume,clear_resume=clear_resume)
    receipt.update(entry_id=result.entry_id,model_name=result.model_name,artifact_sha256=plan["artifact_sha256"],
                   bytes_uploaded=result.bytes_uploaded,md5_verified=result.md5_verified,is_final=result.is_final)
    write_json(receipt_path,receipt)
    status()
    return 0


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("action",choices=["upload","status"])
    parser.add_argument("--work",type=Path,required=True)
    parser.add_argument("--revision",required=True)
    args=parser.parse_args()
    try:
        raise SystemExit(run(args))
    except Exception as error:
        result={"success":False,"error_type":type(error).__name__,"http_status":getattr(error,"status",None)}
        code=getattr(error,"code",None)
        if isinstance(code,str) and re.fullmatch(r"[a-z_]{1,64}",code):
            result["error_code"]=code
        write_json(args.work / "audit/official-error.json",result)
        print(json.dumps(result),flush=True)
        raise SystemExit(1)
