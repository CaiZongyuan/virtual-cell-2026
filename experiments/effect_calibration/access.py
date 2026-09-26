"""Query live submission eligibility without printing credentials or profiles."""

import argparse
import datetime
import json
import os
from pathlib import Path
import sys


def credentials():
    value=json.loads(sys.stdin.readline())
    if not isinstance(value.get("token"),str) or not value["token"]:
        raise ValueError("Missing credential on stdin")
    if value.get("https_proxy"):
        os.environ["HTTPS_PROXY"]=value["https_proxy"]
        os.environ["HTTP_PROXY"]=value["https_proxy"]
    return value["token"]


def check(token):
    from vcc import api

    endpoint="https://virtualcellchallenge.org"
    me=api.get_me(endpoint,token)
    identity=me.get("identity",me)
    if not isinstance(identity.get("can_submit"),bool):
        raise ValueError(f"Unknown eligibility schema; keys={sorted(me)}")
    limits=api.get_limits(endpoint,token)
    if not isinstance(limits.get("limit_reached"),bool):
        raise ValueError("Unknown daily-allowance schema")
    return {"checked_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "can_submit":identity["can_submit"],"limit_reached":limits["limit_reached"],
            "approved":identity.get("approved"),"identity_verified":identity.get("identity_verified"),
            "blockers":identity.get("blockers",[]),"method":"live get_me and get_limits; no offline identity cache"}


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    token=credentials()
    try:
        result=check(token)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2)+"\n")
        print(json.dumps(result),flush=True)
    except Exception as error:
        # Exception bodies stay private; only the failure class crosses stdout.
        print(json.dumps({"success":False,"error_type":type(error).__name__,
                          "http_status":getattr(error,"status",None),
                          "error_code":getattr(error,"code",None)}),flush=True)
        raise SystemExit(1)
