"""Export frozen reliability candidates using canonical H1 controls and decoder."""

import argparse
import json
from pathlib import Path
import zlib

import h5py
import numpy as np
import pandas as pd
from scipy import sparse

from campaign import save_json, sha
from data import cache_controls, gene_names
from effects import transfer_counts
from export import Writer


def run(args):
    protocol = json.loads((args.previous / "protocol.json").read_text())
    info = json.loads((args.work / "effects.json").read_text())
    arm = "shrunk" if args.arm == "state" else args.arm
    model_path = args.work / f"{arm}.npz"
    if sha(model_path) != info["candidate_hashes"][arm] or sha(args.previous / "protocol.json") != info["protocol_sha256"]:
        raise ValueError("Frozen candidate or gene protocol changed")
    with np.load(model_path) as archive:
        tables = {k: archive[k] for k in archive.files}
    targets = sorted(pd.read_csv(args.previous / "h1-benchmark/benchmark/reference_cells.csv")["target_gene"].unique())
    if len(targets) != 126:
        raise ValueError("Canonical H1 panel changed")
    genes = protocol["h1_genes"]
    positions = {g: i for i, g in enumerate(protocol["genes"])}
    selected = np.array([positions[g] for g in genes])
    lookup = {t: i for i, t in enumerate(info["targets"])}
    controls_path = args.previous / "h1-benchmark/h1_controls.h5ad"
    contract = {"arm": args.arm, "panel": "h1", "seed": args.seed, "effects_sha256": sha(model_path),
                "fit_sha256": sha(args.work / "fit.json"), "protocol_sha256": info["protocol_sha256"],
                "controls_sha256": sha(controls_path), "source_revision": args.revision,
                "prior_strength": .5, "residual_strength": .1 if args.arm == "state" else 0}
    residual = None
    if args.arm == "state":
        from residual import ResidualPredictor
        residual = ResidualPredictor(args)
        contract["checkpoint_sha256"] = sha(args.work / "state/final.pt")
    output = args.work / "predictions" / f"{args.arm}-seed{args.seed}.h5ad"
    output.parent.mkdir(parents=True, exist_ok=True)
    writer = Writer(output, genes, [{"target_gene": t} for t in targets for _ in range(400)], contract=contract)
    with h5py.File(controls_path) as h:
        if list(gene_names(h)) != genes:
            raise ValueError("H1 control axis mismatch")
        cached = cache_controls(h)
        if cached is None:
            raise ValueError("H1 controls exceed resident memory allowance")
        for k, target in enumerate(targets):
            seed = zlib.crc32(f"h1-control-baseline-v1:{target}".encode())
            ids = np.sort(np.random.default_rng(seed).choice(cached.shape[0], 400, replace=False))
            raw = cached[ids]
            raw = raw.toarray() if sparse.issparse(raw) else np.asarray(raw)
            if target in lookup:
                i = lookup[target]
                delta, mask = tables["deltas"][i, selected], tables["masks"][i, selected]
                if residual is not None:
                    delta = .5 * np.clip(delta, -np.log(4), np.log(4)) + .1 * residual.predict(raw, selected, target)[selected]
            else:
                delta, mask = np.zeros(len(genes)), np.zeros(len(genes), bool)
            rng = np.random.default_rng(zlib.crc32(f"{args.seed}:{target}".encode()))
            writer.append(transfer_counts(raw, delta, mask, rng, shrink=1 if residual else .5))
            if (k+1) % 10 == 0:
                print(json.dumps({"arm": args.arm, "targets": k+1, "total": len(targets)}), flush=True)
    result = writer.finish()
    result.update(contract, sha256=sha(output))
    save_json(output.with_suffix(".json"), result)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("/mnt/e/vcc2026-data"))
    parser.add_argument("--arm", choices=["expanded", "shrunk", "state"], required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--revision", required=True)
    run(parser.parse_args())
