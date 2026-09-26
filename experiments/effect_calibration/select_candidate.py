"""Select only complete trials and issue a reproducible submission release."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import time

from summarize import METRICS, protocol_identity


ARMS = {"conservative":"conservative-score", "mean_shift":"mean_shift-score", "state_residual":"state-score"}


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream,"sha256").hexdigest()


def read_result(folder, baseline, prediction=None):
    manifest=json.loads((folder / "manifest.json").read_text())
    if protocol_identity(manifest)!=protocol_identity(baseline) or manifest["controls"]!=baseline["controls"]:
        raise ValueError(f"Different evaluator/control protocol: {folder}")
    for item in manifest["outputs"].values():
        if sha(folder / item["path"])!=item["sha256"]:
            raise ValueError(f"Changed scoring output: {folder}")
    if prediction is not None and sha(prediction)!=manifest["prediction"]["sha256"]:
        raise ValueError("Prediction changed after scoring")
    values={}
    for name,column in [("scores","from_replicate"),("aggregates","raw_value")]:
        with (folder / f"{name}.csv").open() as stream:
            values[name]={METRICS[row["metric"]]:float(row[column]) for row in csv.DictReader(stream) if row["metric"] in METRICS}
    scaled,raw=values["scores"],values["aggregates"]
    if len(scaled)!=7 or len(raw)!=6 or not all(math.isfinite(v) for v in [*scaled.values(),*raw.values()]):
        raise ValueError("Incomplete/non-finite metrics")
    if not math.isclose(scaled["avg_score"],sum(v for k,v in scaled.items() if k!="avg_score")/6,abs_tol=1e-12):
        raise ValueError("Composite is not the six-metric average")
    return {"score":scaled["avg_score"],"scaled":scaled,"raw":raw,
            "scores_sha256":manifest["outputs"]["scores"]["sha256"],
            "prediction_sha256":manifest["prediction"].get("sha256"),"status":"valid"}


def require_stage(work,name):
    status=json.loads((work / "status" / f"{name}.json").read_text())
    if status["exit_code"]!=0:
        raise ValueError(f"Stage did not succeed: {name}")
    return status


def select(args):
    selection=args.work / "selection.json"
    if selection.exists():
        raise FileExistsError("Selection already frozen; inspect rather than reselect")
    baseline=json.loads((args.work / "evaluation/control/manifest.json").read_text())
    results={"control":read_result(args.work / "evaluation/control",baseline),
             "incumbent":read_result(args.work / "evaluation/incumbent",baseline,args.campaign / "predictions/empirical.h5ad")}
    incumbent=results["incumbent"]
    eligible=["incumbent"]
    for arm,stage in ARMS.items():
        rejected=args.work / "rejections" / f"{arm}.json"
        if rejected.exists():
            results[arm]={"status":"rejected","reason":json.loads(rejected.read_text())}
            continue
        status=require_stage(args.work,stage)
        generated=json.loads((args.work / "predictions" / f"{arm}.json").read_text())
        checkpoint=sha(args.work / "state/final.pt") if arm=="state_residual" else None
        if (generated["arm"]!=arm or generated["decoding_seed"]!=42 or generated["panel"]!="h1"
                or generated["effects_sha256"]!=sha(args.work / "effects.npz")
                or generated["fit_sha256"]!=sha(args.work / "fit.json")
                or generated.get("checkpoint_sha256")!=checkpoint):
            raise ValueError(f"Scored candidate and current predictor differ: {arm}")
        result=read_result(args.work / "evaluation" / arm,baseline,args.work / "predictions" / f"{arm}.h5ad")
        result.update(stage=status["stage"],score_elapsed_seconds=status["elapsed_seconds"])
        result["gate_passed"]=(result["score"]>=incumbent["score"]+0.01 and
                               result["raw"]["MSE"]<=incumbent["raw"]["MSE"] and
                               result["raw"]["NMAE"]<=incumbent["raw"]["NMAE"]*1.1)
        results[arm]=result
        if result["gate_passed"]:
            eligible.append(arm)
    best=max(eligible,key=lambda arm:results[arm]["score"])
    value={"selected_arm":best,"selected_at_unix":time.time(),"results":results,
           "effects_sha256":sha(args.work / "effects.npz"),"fit_sha256":sha(args.work / "fit.json"),
           "checkpoint_sha256":sha(args.work / "state/final.pt") if best=="state_residual" else None,
           "checkpoint_masks_sha256":sha(args.work / "state/masks.npz") if best=="state_residual" else None,
           "selection_seed":42,"confirmation_seed":43,"official_score":False,
           "confirmation_scope":"decoding seed only; canonical H1 control cells remain fixed",
           "jurkat_used_this_round":False}
    selection.write_text(json.dumps(value,indent=2)+"\n")
    print(json.dumps({"selected_arm":best,"scores":{k:v.get("score") for k,v in results.items()}}),flush=True)


def release(args):
    output=args.work / "release.json"
    if output.exists():
        raise FileExistsError("Release already issued")
    selection=json.loads((args.work / "selection.json").read_text())
    if selection["effects_sha256"]!=sha(args.work / "effects.npz") or selection["fit_sha256"]!=sha(args.work / "fit.json"):
        raise ValueError("Frozen predictor changed")
    if selection["selected_arm"]=="state_residual":
        if selection["checkpoint_sha256"]!=sha(args.work / "state/final.pt") or selection["checkpoint_masks_sha256"]!=sha(args.work / "state/masks.npz"):
            raise ValueError("Frozen State checkpoint or masks changed")
    require_stage(args.work,"confirmation-score")
    exported=json.loads((args.work / "predictions/confirmation.json").read_text())
    if (exported["arm"]!=selection["selected_arm"] or exported["decoding_seed"]!=43
            or exported["panel"]!="h1" or exported["effects_sha256"]!=selection["effects_sha256"]
            or exported["fit_sha256"]!=selection["fit_sha256"]
            or exported.get("checkpoint_sha256")!=selection["checkpoint_sha256"]):
        raise ValueError("Confirmation does not use the frozen candidate and second decoding seed")
    baseline=json.loads((args.work / "evaluation/control/manifest.json").read_text())
    confirmation=read_result(args.work / "evaluation/confirmation",baseline,args.work / "predictions/confirmation.h5ad")
    first=selection["results"][selection["selected_arm"]]
    control=selection["results"]["control"]
    passed=(all(r["score"]>=control["score"]+0.05 and
                all(r["raw"][metric]<2*control["raw"][metric] for metric in ["MSE","NMAE"])
                for r in [first,confirmation]) and confirmation["score"]>=first["score"]-0.01)
    value={"released":passed,"recorded_at_unix":time.time(),"selected_arm":selection["selected_arm"],
           "selection_sha256":sha(args.work / "selection.json"),"effects_sha256":selection["effects_sha256"],
           "fit_sha256":selection["fit_sha256"],"checkpoint_sha256":selection["checkpoint_sha256"],
           "first_seed":first,"confirmation":confirmation,"control":control,
           "user_authorization":"2026-09-26: continue optimization and start official submissions after sufficient local trials",
           "submission_count_limit_this_round":1,"remaining_requirements":["complete ABC export and fresh full prep","live eligibility and daily allowance","artifact and provenance verification"]}
    output.write_text(json.dumps(value,indent=2)+"\n")
    print(json.dumps({"released":passed,"selected_arm":selection["selected_arm"],"confirmation_score":confirmation["score"]}),flush=True)


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("action",choices=["select","release"])
    parser.add_argument("--work",type=Path,required=True)
    parser.add_argument("--campaign",type=Path)
    args=parser.parse_args()
    if args.action=="select" and args.campaign is None:
        parser.error("--campaign is required for selection")
    {"select":select,"release":release}[args.action](args)
