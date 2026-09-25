"""Signed State corrections around a fixed empirical effect predictor."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np
import torch

from calibration import aggregate
from campaign import SOURCES, CONTEXTS, contrast, load_state, save_json, sha
from data import PreparedSource
from effects import log_effect, matched_means
from model import expression_from_counts, normalized_features


def signed_model(args, initialize=False):
    model, features, protocol, provenance = load_state(args)
    if len(model.project_out) != 1 or not isinstance(model.project_out[0],torch.nn.Linear):
        raise ValueError("Expected the audited single-linear State output head")
    model.relu = torch.nn.Identity()
    if initialize:
        with torch.no_grad():
            model.project_out[0].weight.zero_()
            model.project_out[0].bias.zero_()
    return model.eval(), features, protocol, provenance


def centered_response(model, controls, target_vectors, anchor_vectors, anchor_masks):
    """Each target and all its anchors receive its own matched control set."""
    n, anchors = len(controls), len(anchor_vectors)
    x = controls[:,None].expand(-1,anchors+1,-1,-1).reshape(n*(anchors+1),64,-1)
    vectors = torch.cat([target_vectors[:,None],anchor_vectors[None].expand(n,-1,-1)],dim=1).reshape(n*(anchors+1),-1)
    raw = contrast(model,x,vectors).reshape(n,anchors+1,-1)
    denominator = anchor_masks.sum(0).clamp_min(1)
    center = (raw[:,1:]*anchor_masks[None]).sum(1)/denominator
    return raw[:,0]-center


def prepare_targets(args):
    with np.load(args.campaign / "effects.npz") as archive:
        tables={k:archive[k] for k in archive.files}
    entries=json.loads((args.campaign / "effects.json").read_text())["entries"]
    valid=[]
    for i,row in enumerate(entries):
        prior,mask=aggregate(row["target"],entries,tables["deltas"],tables["masks"],row["context"])
        mask &= tables["masks"][i]
        if mask.any():
            valid.append({"index":i,"source":row["source"],"target":row["target"],
                          "prior":np.clip(prior,-np.log(4),np.log(4)),"mask":mask,
                          "residual":np.clip(tables["deltas"][i],-np.log(4),np.log(4))-0.2*np.clip(prior,-np.log(4),np.log(4))})
    lookup={(r["source"],r["target"]):r for r in valid}
    common=set.intersection(*[{r["target"] for r in valid if r["source"]==s} for s in SOURCES])
    if len(common)<4:
        raise ValueError("Four anchors measured in all training sources are required")
    anchors=sorted(np.random.default_rng(42).choice(sorted(common),4,replace=False).tolist())
    source_masks={s:np.stack([lookup[(s,t)]["mask"] for t in anchors]) for s in SOURCES}
    centers={}
    for source in SOURCES:
        mask=source_masks[source]
        values=np.stack([lookup[(source,t)]["residual"] for t in anchors])
        centers[source]=np.divide((values*mask).sum(0),mask.sum(0),out=np.zeros(values.shape[1]),where=mask.sum(0)>0)
    for row in valid:
        row["mask"] &= source_masks[row["source"]].any(0)
        row["centered"]=(row["residual"]-centers[row["source"]]).astype(np.float32)
        weight=np.sqrt(tables["controls"][row["index"]]+0.1)*row["mask"]
        row["weight"]=(weight/weight.mean()).astype(np.float32)
    return valid,lookup,anchors,source_masks,tables


def train(args):
    import swanlab

    torch.set_num_threads(4)
    torch.manual_seed(42)
    torch.cuda.manual_seed_all(42)
    output=args.work / args.output_subdir
    output.mkdir(parents=True,exist_ok=False)
    valid,lookup,anchors,source_masks,tables=prepare_targets(args)
    sources={s:PreparedSource(args.previous / "prepared" / s) for s in SOURCES}
    groups={(s,g["target"]):g for s,source in sources.items() for g in source.groups}
    candidates={s:[r["target"] for r in valid if r["source"]==s] for s in SOURCES}
    model,features,protocol,provenance=signed_model(args,initialize=True)
    for name,p in model.named_parameters():
        p.requires_grad_(name.startswith(("pert_encoder.","project_out.")) or
                         (name.startswith("transformer_backbone.") and any(f"layers.{i}." in name for i in [6,7])))
    optimizer=torch.optim.AdamW([
        {"params":[p for n,p in model.named_parameters() if p.requires_grad and not n.startswith("transformer_backbone.")],"lr":1e-4},
        {"params":[p for n,p in model.named_parameters() if p.requires_grad and n.startswith("transformer_backbone.")],"lr":1e-5},
    ],weight_decay=0)
    vectors={t:normalized_features(features,[t])[0].cuda() for t in sorted({r["target"] for r in valid})}
    anchor_vectors=torch.stack([vectors[t] for t in anchors])
    union_mask=np.logical_or.reduce([r["mask"] for r in valid])
    inference_anchors=np.logical_or.reduce([source_masks[s] for s in SOURCES])
    provenance.update(steps=args.steps,seed=42,source_revision=args.revision,anchors=anchors,
                      eligible_conditions=len(valid),eligible_targets=len(vectors),
                      trainable_parameters=sum(p.numel() for p in model.parameters() if p.requires_grad),
                      initialization="existing all-source descendant; signed output head reset to zero",
                      prior_strength=0.2,residual_strength=0.1,pairwise_weight=0.5,
                      source_effects_sha256=sha(args.campaign / "effects.npz"),
                      target_center="four fixed training anchors, per-gene measured masks; same centering for predictions and labels",
                      background_holdout_claim=False)
    save_json(output / "provenance.json",provenance)
    np.savez(output / "masks.npz",supervised=union_mask,anchors=inference_anchors)
    swanlab.init(project="virtual-cell-2026",experiment_name=f"signed-residual-{args.output_subdir}-seed42",
                 config=provenance,logdir=str(args.work / "swanlog"),mode="local")
    development={}

    def desired(source_name,target,split):
        row=lookup[(source_name,target)]
        if split=="training":
            return row["centered"]
        key=(source_name,target)
        if key not in development:
            source=sources[source_name]
            control,treated=matched_means(source,groups[key],split="development")
            delta=np.clip(log_effect(control,treated,source.measured),-np.log(4),np.log(4))
            development[key]=(delta-0.2*row["prior"]).astype(np.float32)
        return development[key]

    def loss(rng,split="training",null_check=False):
        name=SOURCES[int(rng.choice(4,p=[1/6,1/6,1/3,1/3]))]
        source=sources[name]
        targets=rng.choice(candidates[name],2,replace=False).tolist()
        raw=[]
        labels=[]
        weights=[]
        if split=="development":
            values=np.stack([desired(name,t,split) for t in anchors])
            mask=source_masks[name]
            dev_center=np.divide((values*mask).sum(0),mask.sum(0),out=np.zeros(values.shape[1]),where=mask.sum(0)>0)
        for target in targets:
            rows=groups[(name,target)][split]
            chosen=rng.choice(rows,64,replace=len(rows)<64)
            controls=[int(rng.choice(source.controls_by_batch[str(b)])) for b in source.row_batches[chosen]]
            raw.append(expression_from_counts(source.counts[controls].toarray()))
            value=desired(name,target,split)
            labels.append(value if split=="training" else value-dev_center)
            weights.append(lookup[(name,target)]["weight"])
        model.measurement_mask.copy_(torch.from_numpy(source.measured.astype(np.float32)).cuda())
        x=torch.from_numpy(np.stack(raw)).cuda()
        target_vectors=torch.stack([vectors[t] for t in targets])
        masks=torch.from_numpy(source_masks[name].astype(np.float32)).cuda()
        with torch.autocast("cuda",dtype=torch.bfloat16):
            prediction=centered_response(model,x,target_vectors,anchor_vectors,masks)
            if null_check:
                null=contrast(model,x,torch.zeros_like(target_vectors))
                if not torch.equal(null,torch.zeros_like(null)):
                    raise ValueError("NTC differential is not exactly zero")
        truth=torch.from_numpy(np.stack(labels).astype(np.float32)).cuda()
        weight=torch.from_numpy(np.stack(weights)).cuda()
        paired_weight=torch.sqrt(weight[0]*weight[1])
        paired_weight=paired_weight/paired_weight.mean().clamp_min(1e-12)
        error=((prediction-truth).square()*weight).mean()
        pair=(((prediction[0]-prediction[1])-(truth[0]-truth[1])).square()*paired_weight).mean()
        baseline=(truth.square()*weight).mean()+0.5*((truth[0]-truth[1]).square()*paired_weight).mean()
        return error+0.5*pair,baseline,prediction

    rng=np.random.default_rng(42)
    start=time.monotonic()
    with (output / "metrics.jsonl").open("w",buffering=1) as log:
        for step in range(1,args.steps+1):
            optimizer.zero_grad(set_to_none=True)
            value,baseline,prediction=loss(rng,null_check=step==1)
            if step==1 and not torch.equal(prediction,torch.zeros_like(prediction)):
                raise ValueError("Zero-initialized correction changed the empirical prior")
            if not torch.isfinite(value):
                raise ValueError("Non-finite training loss")
            value.backward()
            norm=torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad],10,error_if_nonfinite=True)
            optimizer.step()
            if step==1 or step%100==0:
                row={"step":step,"loss":value.item(),"zero_correction_loss":baseline.item(),
                     "grad_norm":float(norm),"elapsed_seconds":time.monotonic()-start,
                     "gpu_peak_bytes":torch.cuda.max_memory_allocated()}
                log.write(json.dumps(row)+"\n")
                swanlab.log({"loss/train":row["loss"],"loss/zero_correction":row["zero_correction_loss"]},step=step)
                print(json.dumps(row),flush=True)
        with torch.inference_mode():
            dev_rng=np.random.default_rng(2026)
            diagnostics=[loss(dev_rng,"development",null_check=i==0)[:2] for i in range(16)]
            dev=float(np.mean([v.item() for v,b in diagnostics]))
            null=float(np.mean([b.item() for v,b in diagnostics]))
        complete={"steps":args.steps,"development_loss":dev,"zero_correction_development_loss":null,
                  "scope":"source held-cell diagnostics, not held-background validation or early stopping",
                  "elapsed_seconds":time.monotonic()-start}
        log.write(json.dumps(complete)+"\n")
    torch.save({"state_dict":model.cpu().state_dict(),"provenance":provenance,
                "gene_axis_sha256":protocol["gene_axis_sha256"]},output / "final.pt")
    save_json(output / "complete.json",complete)
    swanlab.finish()
    print(json.dumps(complete),flush=True)


class ResidualPredictor:
    def __init__(self,args):
        torch.set_num_threads(4)
        self.model,self.features,self.protocol,_=signed_model(args)
        checkpoint=torch.load(args.work / "state/final.pt",map_location="cpu",weights_only=False)
        if checkpoint["gene_axis_sha256"]!=self.protocol["gene_axis_sha256"]:
            raise ValueError("Residual checkpoint gene axis mismatch")
        self.model.load_state_dict(checkpoint["state_dict"],strict=True)
        self.anchors=checkpoint["provenance"]["anchors"]
        del checkpoint
        with np.load(args.work / "state/masks.npz") as masks:
            self.supervised=masks["supervised"]
            self.anchor_masks=torch.from_numpy(masks["anchors"].astype(np.float32)).cuda()
        self.anchor_vectors=normalized_features(self.features,self.anchors).cuda()

    def predict(self,raw,selected,target):
        if target=="non-targeting":
            return np.zeros(len(self.protocol["genes"]))
        counts=np.zeros((448,len(self.protocol["genes"])),np.float32)
        counts[:,selected]=np.concatenate([raw,raw[:48]])
        measured=np.zeros(len(self.protocol["genes"]),np.float32)
        measured[selected]=1
        self.model.measurement_mask.copy_(torch.from_numpy(measured).cuda())
        controls=torch.from_numpy(expression_from_counts(counts)).cuda().reshape(7,64,-1)
        vectors=normalized_features(self.features,[target]).cuda().expand(7,-1)
        with torch.inference_mode(),torch.autocast("cuda",dtype=torch.bfloat16):
            value=centered_response(self.model,controls,vectors,self.anchor_vectors,self.anchor_masks).mean(0).cpu().numpy()
        return np.where(self.supervised & measured.astype(bool),np.clip(value,-np.log(2),np.log(2)),0)


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--previous",type=Path,required=True)
    parser.add_argument("--campaign",type=Path,required=True)
    parser.add_argument("--work",type=Path,required=True)
    parser.add_argument("--root",type=Path,default=Path("/mnt/e/vcc2026-data"))
    parser.add_argument("--steps",type=int,default=6000)
    parser.add_argument("--output-subdir",default="state")
    parser.add_argument("--revision",required=True)
    train(parser.parse_args())
