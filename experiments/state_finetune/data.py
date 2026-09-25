"""Bounded source preparation and matched-control condition sampling."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import time

import h5py
import numpy as np
from scipy import sparse


def csv_column(path, header=None):
    with Path(path).open() as stream:
        rows = list(csv.reader(stream))
    if header is not None:
        position = rows[0].index(header)
        return [row[position] for row in rows[1:]]
    return [row[0] for row in rows]


def h5_column(group, key):
    field = group[key]
    if isinstance(field, h5py.Group):
        if "values" in field and "mask" in field:
            if field["mask"][:].any():
                raise ValueError(f"Missing nullable labels: {key}")
            values = field["values"]
            return values.asstr()[:] if values.dtype.kind in "OSU" else values[:].astype(str)
        categories = field["categories"].asstr()[:] if field["categories"].dtype.kind in "OSU" else field["categories"][:].astype(str)
        codes = field["codes"][:]
        if (codes < 0).any():
            raise ValueError(f"Missing categorical labels: {key}")
        return categories[codes]
    return field.asstr()[:] if field.dtype.kind in "OSU" else field[:].astype(str)


def gene_names(handle):
    group = handle["var"]
    index = group.attrs.get("_index", "_index")
    if isinstance(index, bytes):
        index = index.decode()
    return h5_column(group, index)


def read_rows(handle, indices):
    indices = np.asarray(indices, dtype=np.int64)
    ordered, inverse = np.unique(indices, return_inverse=True)
    matrix = handle["X"]
    if isinstance(matrix, h5py.Dataset):
        values = matrix[ordered]
    else:
        pointers = matrix["indptr"][:]
        rows = []
        width = int(matrix.attrs["shape"][1])
        for row in ordered:
            start, end = int(pointers[row]), int(pointers[row + 1])
            rows.append(sparse.csr_matrix((matrix["data"][start:end], matrix["indices"][start:end], [0, end-start]), shape=(1, width)))
        values = sparse.vstack(rows).toarray()
    return values[inverse]


def cache_controls(handle, max_bytes=4 * 2**30):
    """Cache the fixed control input, never the much larger prediction matrix."""
    matrix = handle["X"]
    if isinstance(matrix, h5py.Dataset):
        required = matrix.size * matrix.dtype.itemsize
        return matrix[:] if required <= max_bytes else None
    required = sum(matrix[name].size * matrix[name].dtype.itemsize for name in ["data", "indices", "indptr"])
    if required > max_bytes:
        return None
    return sparse.csr_matrix((matrix["data"][:], matrix["indices"][:], matrix["indptr"][:]), shape=tuple(matrix.attrs["shape"]))


def prepare(root: Path, work: Path, source: str, per_condition=256, controls_per_batch=1024):
    destination = work / "prepared" / source
    if (destination / "manifest.json").exists():
        print(f"{source}: already prepared", flush=True)
        return
    axis = json.loads((work / "protocol.json").read_text())
    genes = axis["genes"]
    target_panel = set(axis["training_targets"])
    positions = {name: index for index, name in enumerate(genes)}
    destination.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)
    with h5py.File(root / "raw" / f"{source}.h5ad", "r") as handle:
        source_genes = list(gene_names(handle))
        if len(source_genes) != len(set(source_genes)):
            raise ValueError("Source has duplicate gene identifiers")
        source_columns = np.array([i for i, name in enumerate(source_genes) if name in positions])
        target_columns = np.array([positions[source_genes[i]] for i in source_columns])
        measured = np.zeros(len(genes), dtype=bool)
        measured[target_columns] = True
        labels = h5_column(handle["obs"], "gene")
        batches = h5_column(handle["obs"], "batch")
        selected, groups, controls_by_batch = [], [], {}
        # Targets are distributed across hundreds of technical batches. Form
        # sets by source/target and match each sampled treated cell's batch to
        # an independently sampled NTC; never require 64 target cells per batch.
        for batch in np.unique(batches):
            batch_rows = np.flatnonzero(batches == batch)
            batch_labels = labels[batch_rows]
            controls = batch_rows[batch_labels == "non-targeting"]
            if len(controls) < 16:
                continue
            chosen_controls = np.sort(rng.choice(controls, min(len(controls), controls_per_batch), replace=False))
            selected.extend(chosen_controls.tolist())
            controls_by_batch[str(batch)] = chosen_controls.tolist()
        eligible = np.isin(batches, list(controls_by_batch))
        for target in sorted(set(labels) & target_panel):
            rows = np.flatnonzero((labels == target) & eligible)
            if len(rows) < 64:
                continue
            chosen = np.sort(rng.choice(rows, min(len(rows), per_condition), replace=False))
            selected.extend(chosen.tolist())
            groups.append({"target": target, "original_rows": chosen.tolist(), "available_cells": len(rows)})
        if not groups:
            raise ValueError(f"No usable conditions in {source}")
        selected = np.array(sorted(set(selected)), dtype=np.int64)
        remap = {int(row): index for index, row in enumerate(selected)}
        for group in groups:
            rows = np.array([remap[row] for row in group.pop("original_rows")])
            rng.shuffle(rows)
            n_dev = max(8, len(rows) // 5)
            group["development"] = rows[:n_dev].tolist()
            group["training"] = rows[n_dev:].tolist()
        controls_by_batch = {batch: [remap[row] for row in rows] for batch, rows in controls_by_batch.items()}
        parts = []
        matrix = handle["X"]
        block_rows = matrix.chunks[0] if isinstance(matrix, h5py.Dataset) and matrix.chunks else 2048
        block_rows = min(block_rows, 4096)
        last_report = time.monotonic()
        for start in range(0, len(labels), block_rows):
            end = min(len(labels), start + block_rows)
            low, high = np.searchsorted(selected, [start, end])
            if low == high:
                continue
            if isinstance(matrix, h5py.Dataset):
                block = matrix[start:end][selected[low:high] - start][:, source_columns]
            else:
                block = read_rows(handle, selected[low:high])[:, source_columns]
            if not np.isfinite(block).all() or (block < 0).any() or not np.equal(block, np.floor(block)).all():
                raise ValueError(f"{source} X is not finite non-negative integer counts")
            local = sparse.csr_matrix(block.astype(np.float32))
            local.eliminate_zeros()
            mapped = sparse.csr_matrix((local.data, target_columns[local.indices], local.indptr), shape=(len(block), len(genes)))
            mapped.sort_indices()
            parts.append(mapped)
            if time.monotonic() - last_report > 20:
                print(json.dumps({"source": source, "rows_scanned": end, "total_rows": len(labels), "selected": int(high)}), flush=True)
                last_report = time.monotonic()
        prepared = sparse.vstack(parts, format="csr")
        if prepared.shape[0] != len(selected) or (np.asarray(prepared.sum(axis=1)).ravel() <= 0).any():
            raise ValueError("Prepared matrix has wrong row count or empty cells")
        sparse.save_npz(destination / "counts.npz", prepared, compressed=False)
        np.save(destination / "measured.npy", measured)
        np.save(destination / "original_rows.npy", selected)
        np.save(destination / "row_batches.npy", batches[selected].astype(str))
        manifest = {"source": source, "shape": list(prepared.shape), "nnz": int(prepared.nnz),
                    "gene_axis_sha256": axis["gene_axis_sha256"], "groups": groups,
                    "controls_by_batch": controls_by_batch,
                    "measured_genes": int(measured.sum()), "seed": 42,
                    "development_split": "disjoint cells within source/batch/target; not a held-out biological background"}
        (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(json.dumps({"source": source, "state": "prepared", "shape": prepared.shape, "conditions": len(groups)}), flush=True)


def protocol(work, root, parent_targets_path):
    from model import load_features, load_parent_targets
    official_genes = csv_column(work / "controls/gene_names.csv", "gene_name")
    h1_genes = csv_column(root / "assets/h1_gene_names.csv")
    official_targets = csv_column(work / "controls/pert_counts.csv", "target_gene")
    h1_targets = csv_column(root / "assets/h1_pert_counts.csv", "target_gene")
    official_set = set(official_genes)
    genes = official_genes + [name for name in h1_genes if name not in official_set]
    if len(genes) != 18536 or len(set(genes)) != len(genes):
        raise ValueError("Unexpected/duplicate challenge and H1 gene axis")
    features = load_features(root / "assets/ESM2_pert_features.pt")
    parent_targets = (json.loads(Path(parent_targets_path).read_text()) if parent_targets_path
                      else load_parent_targets(root / "assets/parent/pert_onehot_map.pt"))
    required = set(official_targets) | set(h1_targets)
    missing = sorted(required - set(features))
    if missing:
        raise ValueError(f"Required targets lack protein features: {missing}")
    candidates = sorted(set(parent_targets) & set(features) - required)
    rng = np.random.default_rng(42)
    rehearsal = rng.choice(candidates, min(256, len(candidates)), replace=False).tolist()
    value = {
        "genes": genes, "official_genes": official_genes, "h1_genes": h1_genes,
        "official_targets": official_targets, "h1_targets": h1_targets,
        "training_targets": sorted(required | set(rehearsal)), "rehearsal_targets": sorted(rehearsal),
        "gene_axis_sha256": hashlib.sha256("\n".join(genes).encode()).hexdigest(),
        "parent_targets": parent_targets, "seed": 42, "cell_set_len": 64,
        "training_sources": ["gwps", "hepg2", "rpe1", "k562"],
        "background_holdout": "H1", "normalization": "log1p(CP10000), measured model-axis genes only",
        "feature_aliases": {"TAZ": {"feature_key": "TAFAZZIN", "ensembl_id": "ENSG00000102125", "hgnc_id": "HGNC:11577"}},
    }
    (work / "protocol.json").write_text(json.dumps(value, indent=2) + "\n")
    print(json.dumps({"genes": len(genes), "targets": len(value["training_targets"]), "feature_coverage": "complete"}), flush=True)


class PreparedSource:
    def __init__(self, path):
        self.manifest = json.loads((path / "manifest.json").read_text())
        self.counts = sparse.load_npz(path / "counts.npz")
        self.measured = np.load(path / "measured.npy")
        self.groups = self.manifest["groups"]
        self.row_batches = np.load(path / "row_batches.npy")
        self.controls_by_batch = self.manifest["controls_by_batch"]

    def sample(self, rng, split="training", size=64):
        group = self.groups[int(rng.integers(len(self.groups)))]
        treatment_rows = rng.choice(group[split], size, replace=len(group[split]) < size)
        control_rows = [int(rng.choice(self.controls_by_batch[str(batch)])) for batch in self.row_batches[treatment_rows]]
        return group["target"], self.counts[control_rows].toarray(), self.counts[treatment_rows].toarray(), self.measured


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["protocol", "prepare"])
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--parent-targets", type=Path)
    parser.add_argument("--source")
    args = parser.parse_args()
    if args.action == "protocol":
        protocol(args.work, args.root, args.parent_targets)
    else:
        prepare(args.root, args.work, args.source)
