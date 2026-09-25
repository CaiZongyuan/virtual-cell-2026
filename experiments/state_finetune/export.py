"""Generate bounded-memory H1/ABC raw-count H5AD predictions."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import anndata as ad
import h5py
import numpy as np
import pandas as pd
from scipy import sparse
import torch

from data import cache_controls, gene_names, h5_column, read_rows
from model import build_model, expression_from_counts, integer_counts, load_features, normalized_features


class Writer:
    def __init__(self, path, genes, rows, resume=False, contract=None):
        if path.exists():
            if not resume:
                raise FileExistsError(path)
            with h5py.File(path, "r") as existing:
                if contract is not None and json.loads(existing.attrs.get("vc2026_export_contract", "null")) != contract:
                    raise ValueError("Resume checkpoint/seed/protocol contract differs or is missing")
                if tuple(existing["X"].attrs["shape"]) != (len(rows), len(genes)) or list(gene_names(existing)) != list(genes):
                    raise ValueError("Resume output has a different gene/row contract")
                for column in rows[0]:
                    if h5_column(existing["obs"], column).tolist() != [row[column] for row in rows]:
                        raise ValueError("Resume output has different observation labels")
            self.path, self.total_rows = path, len(rows)
            self.file = h5py.File(path, "r+")
            matrix = self.file["X"]
            self.values, self.indices, self.pointers = matrix["data"], matrix["indices"], matrix["indptr"]
            valid = np.flatnonzero(self.pointers[:] > 0)
            self.row = (int(valid[-1]) // 400) * 400 if len(valid) else 0
            self.nnz = int(self.pointers[self.row])
            self.values.resize((self.nnz,))
            self.indices.resize((self.nnz,))
            self.pointers[self.row+1:] = 0
            self.file.flush()
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.total_rows = len(rows)
        obs = pd.DataFrame(rows, index=[f"pred_{i:09d}" for i in range(len(rows))])
        for column in obs:
            obs[column] = pd.Categorical(obs[column])
        metadata = ad.AnnData(obs=obs, var=pd.DataFrame(index=genes), shape=(len(rows), len(genes)))
        metadata.write_h5ad(path)
        self.file = h5py.File(path, "r+")
        if contract is not None:
            self.file.attrs["vc2026_export_contract"] = json.dumps(contract, sort_keys=True)
        matrix = self.file.create_group("X")
        matrix.attrs.update({"encoding-type": "csr_matrix", "encoding-version": "0.1.0", "shape": (len(rows), len(genes))})
        self.values = matrix.create_dataset("data", shape=(0,), maxshape=(None,), dtype="int32", chunks=(262144,), compression="lzf")
        self.indices = matrix.create_dataset("indices", shape=(0,), maxshape=(None,), dtype="int32", chunks=(262144,), compression="lzf")
        self.pointers = matrix.create_dataset("indptr", shape=(len(rows)+1,), dtype="int64")
        self.row, self.nnz = 0, 0

    def append(self, counts):
        if not np.isfinite(counts).all() or (counts < 0).any() or not np.equal(counts, np.floor(counts)).all():
            raise ValueError("Invalid count values")
        totals = counts.sum(axis=1, dtype=np.int64)
        if (totals <= 0).any() or (totals > 1_000_000).any():
            raise ValueError("Invalid cell depths")
        matrix = sparse.csr_matrix(counts, dtype=np.int32)
        matrix.eliminate_zeros()
        end = self.nnz + matrix.nnz
        if end > 4_750_000_000:
            raise ValueError("Submission stored-entry limit exceeded")
        self.values.resize((end,))
        self.indices.resize((end,))
        self.values[self.nnz:end] = matrix.data
        self.indices[self.nnz:end] = matrix.indices
        self.pointers[self.row+1:self.row+len(counts)+1] = matrix.indptr[1:].astype(np.int64) + self.nnz
        self.row += len(counts)
        self.nnz = end
        self.file.flush()

    def finish(self):
        if self.row != self.total_rows:
            raise ValueError("Incomplete output row count")
        self.file.close()
        return {"path": str(self.path), "rows": self.row, "stored_entries": self.nnz,
                "bytes": self.path.stat().st_size}


def templates(handle, rng):
    # AnnData categorical groups have two child datasets, so take row count
    # from X shape instead of metadata len(group).
    matrix = handle["X"]
    row_count = matrix.shape[0] if isinstance(matrix, h5py.Dataset) else int(matrix.attrs["shape"][0])
    if "ntc_id" in handle["obs"]:
        labels = h5_column(handle["obs"], "ntc_id")
        groups = np.unique(labels)
        quotas = np.full(len(groups), 400 // len(groups))
        quotas[rng.permutation(len(groups))[:400 % len(groups)]] += 1
        chosen = np.concatenate([rng.choice(np.flatnonzero(labels == group), int(quota), replace=False)
                                 for group, quota in zip(groups, quotas)])
        rng.shuffle(chosen)
    else:
        chosen = rng.choice(row_count, 400, replace=False)
    extra = rng.choice(np.setdiff1d(np.arange(row_count), chosen), 48, replace=False)
    return np.concatenate([chosen, extra])


def run(args):
    torch.set_num_threads(6)
    protocol = json.loads((args.work / "protocol.json").read_text())
    features = load_features(args.root / "assets/ESM2_pert_features.pt")
    model, _ = build_model(args.work / "upstream/state", args.root / "assets/parent/best.ckpt",
                           protocol["genes"], features, protocol["parent_targets"])
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    if checkpoint["protocol"]["gene_axis_sha256"] != protocol["gene_axis_sha256"]:
        raise ValueError("Checkpoint gene axis mismatch")
    model.load_state_dict(checkpoint["state_dict"], strict=True)
    model.cuda().eval()
    supervised = np.load(args.checkpoint.parent / "supervised.npy")
    position = {name: index for index, name in enumerate(protocol["genes"])}
    if args.panel == "h1":
        reference = pd.read_csv(args.work / "h1-benchmark/benchmark/reference_cells.csv")
        target_column = "target_gene" if "target_gene" in reference else "target"
        targets = sorted(reference[target_column].unique())
        if len(targets) != 126:
            raise ValueError("Unexpected H1 canonical target panel")
        contexts = [("H1", args.work / "h1-benchmark/h1_controls.h5ad")]
        genes = protocol["h1_genes"]
        rows = [{"target_gene": target} for target in targets for _ in range(400)]
    else:
        targets = protocol["official_targets"]
        contexts = []
        for context in ["A", "B", "C"]:
            candidates = []
            for path in (args.work / "controls").rglob("*.h5ad"):
                with h5py.File(path) as handle:
                    if set(h5_column(handle["obs"], "context")) == {context}:
                        candidates.append(path)
            if len(candidates) != 1:
                raise ValueError(f"Could not identify controls for {context}")
            contexts.append((context, candidates[0]))
        genes = protocol["official_genes"]
        rows = [{"context": context, "target_gene": target} for context, _ in contexts for target in targets for _ in range(400)]
    export_positions = np.array([position[name] for name in genes])
    with args.checkpoint.open("rb") as stream:
        checkpoint_sha = hashlib.file_digest(stream, "sha256").hexdigest()
    contract = {"checkpoint_sha256": checkpoint_sha, "seed": args.seed, "panel": args.panel,
                "gene_axis_sha256": protocol["gene_axis_sha256"]}
    writer = Writer(args.output, genes, rows, resume=args.resume, contract=contract)
    completed_conditions = writer.row // 400
    condition_index = 0
    with torch.inference_mode():
        for context, path in contexts:
            with h5py.File(path) as handle:
                cached = cache_controls(handle)
                control_genes = list(gene_names(handle))
                if control_genes != genes:
                    raise ValueError("Control axis differs from export axis")
                mask = np.zeros(len(position), dtype=np.float32)
                mask[export_positions] = 1
                model.measurement_mask.copy_(torch.from_numpy(mask).cuda())
                for target in targets:
                    if condition_index < completed_conditions:
                        condition_index += 1
                        continue
                    seed = int.from_bytes(hashlib.sha256(f"{args.seed}:{context}:{target}".encode()).digest()[:8], "little")
                    rng = np.random.default_rng(seed)
                    selected_rows = templates(handle, rng)
                    raw = read_rows(handle, selected_rows) if cached is None else cached[selected_rows]
                    if sparse.issparse(raw):
                        raw = raw.toarray()
                    counts = np.zeros((448, len(position)), dtype=np.float32)
                    counts[:, export_positions] = raw
                    normalized = expression_from_counts(counts)
                    feature = normalized_features(features, [target]).expand(64, -1).cuda()
                    parts = []
                    for start in range(0, 448, 64):
                        batch = {"ctrl_cell_emb": torch.from_numpy(normalized[start:start+64]).cuda(), "pert_emb": feature}
                        with torch.autocast("cuda", dtype=torch.bfloat16):
                            result = model(batch)
                        parts.append(result.float().cpu().numpy()[:, export_positions])
                    prediction = np.concatenate(parts)[:400]
                    output = integer_counts(prediction, raw[:400], supervised[export_positions], rng)
                    writer.append(output)
                    condition_index += 1
                    print(json.dumps({"context": context, "target": target, "rows_written": writer.row, "nnz": writer.nnz}), flush=True)
    result = writer.finish()
    result.update({"checkpoint": str(args.checkpoint), "checkpoint_sha256": checkpoint_sha,
                   "seed": args.seed, "panel": args.panel,
                   "supervised_genes": int(supervised[export_positions].sum()),
                   "ntc_fallback_genes": int((~supervised[export_positions]).sum())})
    args.output.with_suffix(".manifest.json").write_text(json.dumps(result, indent=2)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--panel", choices=["h1", "abc"], required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--resume", action="store_true")
    run(parser.parse_args())
