"""Export frozen candidates to canonical H1 or complete official ABC inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zlib

import h5py
import numpy as np
import pandas as pd
from scipy import sparse

from calibration import mean_shift_counts
from campaign import save_json, sha
from data import cache_controls, gene_names, h5_column
from effects import cp10k, transfer_counts
from export import Writer, templates


def control_mean(matrix):
    total = np.zeros(matrix.shape[1], dtype=np.float64)
    for start in range(0, matrix.shape[0], 1024):
        total += np.asarray(cp10k(matrix[start:start+1024]).sum(axis=0)).ravel()
    return total/matrix.shape[0]


def run(args):
    protocol = json.loads((args.previous / "protocol.json").read_text())
    effect_info = json.loads((args.work / "effects.json").read_text())
    fit = json.loads((args.work / "fit.json").read_text())
    with np.load(args.work / "effects.npz") as archive:
        tables = {k: archive[k] for k in archive.files}
    lookup = {target:i for i,target in enumerate(effect_info["targets"])}
    position = {gene:i for i,gene in enumerate(protocol["genes"])}
    if effect_info["protocol_sha256"] != sha(args.previous / "protocol.json"):
        raise ValueError("Model-axis protocol changed")
    if args.panel == "h1":
        panel = pd.read_csv(args.previous / "h1-benchmark/benchmark/reference_cells.csv")
        key = "target_gene" if "target_gene" in panel else "target"
        targets = sorted(panel[key].unique())
        if len(targets) != 126:
            raise ValueError("H1 target panel changed")
        contexts = [("H1",args.previous / "h1-benchmark/h1_controls.h5ad")]
        genes = protocol["h1_genes"]
        rows = [{"target_gene":target} for target in targets for _ in range(400)]
    else:
        targets, genes = protocol["official_targets"], protocol["official_genes"]
        contexts = []
        for context in ["A","B","C"]:
            candidates = []
            for path in (args.previous / "controls").rglob("*.h5ad"):
                with h5py.File(path) as handle:
                    if set(h5_column(handle["obs"],"context")) == {context}:
                        candidates.append(path)
            if len(candidates) != 1:
                raise ValueError(f"Ambiguous/missing controls for {context}")
            contexts.append((context,candidates[0]))
        if len(targets) != 300 or len(genes) != 18533:
            raise ValueError("Official panel changed")
        rows = [{"context":context,"target_gene":target} for context,_ in contexts for target in targets for _ in range(400)]
    selected = np.asarray([position[g] for g in genes])
    strength = {"incumbent":0.5,"conservative":0.2,"mean_shift":fit["additive_strength"],"state_residual":1.0}[args.arm]
    contract = {"arm":args.arm,"panel":args.panel,"decoding_seed":args.seed,
                "strength":strength,"effects_sha256":sha(args.work / "effects.npz"),
                "fit_sha256":sha(args.work / "fit.json"),"protocol_sha256":effect_info["protocol_sha256"],
                "controls_sha256":{context:sha(path) for context,path in contexts},
                "control_sampling":"canonical H1; guide-stratified ABC with fixed seed 42"}
    residual = None
    if args.arm == "state_residual":
        from residual import ResidualPredictor
        residual = ResidualPredictor(args)
        contract["checkpoint_sha256"] = sha(args.work / "state/final.pt")
        contract["residual_weight"] = 0.1
        contract["prior_strength"] = 0.2
    writer = Writer(args.output,genes,rows,resume=args.resume,contract=contract)
    completed = writer.row // 400
    condition = 0
    diagnostics = []
    for context,path in contexts:
        with h5py.File(path) as handle:
            if list(gene_names(handle)) != genes:
                raise ValueError(f"Control gene axis mismatch: {context}")
            cached = cache_controls(handle)
            if cached is None:
                raise ValueError("Control input exceeds the 4 GiB resident bound")
            mean = control_mean(cached) if args.arm == "mean_shift" else None
            for target in targets:
                if condition < completed:
                    condition += 1
                    continue
                if args.panel == "h1":
                    seed = zlib.crc32(f"h1-control-baseline-v1:{target}".encode())
                    indices = np.sort(np.random.default_rng(seed).choice(cached.shape[0],400,replace=False))
                else:
                    seed = int.from_bytes(hashlib.sha256(f"42:{context}:{target}".encode()).digest()[:8],"little")
                    indices = templates(handle,np.random.default_rng(seed))[:400]
                raw = cached[indices]
                raw = raw.toarray() if sparse.issparse(raw) else np.asarray(raw)
                rng = np.random.default_rng(zlib.crc32(f"{args.seed}:{target}".encode()) if args.panel == "h1"
                                             else int.from_bytes(hashlib.sha256(f"{args.seed}:{context}:{target}:decode".encode()).digest()[:8],"little"))
                if target in lookup:
                    i = lookup[target]
                    measured = tables["masks"][i,selected]
                    delta = tables["mean_shifts" if args.arm == "mean_shift" else "log_deltas"][i,selected]
                    if residual is not None:
                        correction = residual.predict(raw,selected,target)
                        delta = np.clip(delta,-np.log(4),np.log(4))*0.2 + 0.1*correction[selected]
                else:
                    measured, delta = np.zeros(len(genes),bool), np.zeros(len(genes))
                if args.arm == "mean_shift":
                    prediction = mean_shift_counts(raw,delta,measured,mean,strength,rng)
                else:
                    prediction = transfer_counts(raw,delta,measured,rng,shrink=strength)
                writer.append(prediction)
                diagnostics.append({"context":context,"target":target,"supervised_genes":int(measured.sum()),
                                    "mean_depth_ratio":float(prediction.sum()/raw.sum())})
                condition += 1
                if condition % 10 == 0 or condition == len(contexts)*len(targets):
                    print(json.dumps({"arm":args.arm,"conditions":condition,"total":len(contexts)*len(targets),"rows":writer.row}),flush=True)
            del cached
    result = writer.finish()
    result.update(contract,sha256=sha(args.output),diagnostics=diagnostics,
                  source_revision=args.revision,resumed_from_conditions=completed)
    save_json(args.output.with_suffix(".json"),result)
    print(json.dumps({k:v for k,v in result.items() if k not in {"diagnostics","controls_sha256"}}),flush=True)


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--previous",type=Path,required=True)
    parser.add_argument("--work",type=Path,required=True)
    parser.add_argument("--root",type=Path,default=Path("/mnt/e/vcc2026-data"))
    parser.add_argument("--arm",choices=["incumbent","conservative","mean_shift","state_residual"],required=True)
    parser.add_argument("--panel",choices=["h1","abc"],default="h1")
    parser.add_argument("--seed",type=int,default=42)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--revision",required=True)
    parser.add_argument("--resume",action="store_true")
    run(parser.parse_args())
