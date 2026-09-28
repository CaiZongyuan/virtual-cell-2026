"""Stream public training counts into means/uncertainties; exclude held-out rows."""

import argparse
import json
from pathlib import Path
import time

import h5py
import numpy as np
from scipy import sparse

from campaign import SOURCES, CONTEXTS, save_json, sha
from data import gene_names, h5_column


def variance_of_mean(total, squared, n):
    mean = total / n[:, None]
    variance = np.maximum(squared / n[:, None] - mean ** 2, 0)
    return mean, variance / np.maximum(n[:, None] - 1, 1)


def aggregate_source(args, source):
    out = args.work / "sources" / source
    out.mkdir(parents=True, exist_ok=False)
    protocol = json.loads((args.previous / "protocol.json").read_text())
    old = args.previous / "prepared" / source
    manifest = json.loads((old / "manifest.json").read_text())
    original = np.load(old / "original_rows.npy")
    excluded = original[np.concatenate([g["development"] for g in manifest["groups"]])]
    start_time = time.monotonic()
    raw_path = args.root / "raw" / f"{source}.h5ad"
    with h5py.File(raw_path) as h:
        source_genes = list(gene_names(h))
        pos = {g: i for i, g in enumerate(protocol["genes"])}
        cols = np.array([i for i, g in enumerate(source_genes) if g in pos])
        dest = np.array([pos[source_genes[i]] for i in cols])
        labels = h5_column(h["obs"], "gene")
        batches, batch_codes = np.unique(h5_column(h["obs"], "batch"), return_inverse=True)
        nt = labels == "non-targeting"
        nt_n = np.bincount(batch_codes[nt], minlength=len(batches))
        eligible_batch = nt_n >= 16
        eligible = eligible_batch[batch_codes]
        eligible[excluded] = False
        candidate = np.isin(labels, protocol["training_targets"]) & eligible & ~nt
        targets, n = np.unique(labels[candidate], return_counts=True)
        targets = targets[n >= 32].tolist()
        target_lookup = {t: i for i, t in enumerate(targets)}
        group = np.full(len(labels), -1, dtype=np.int32)
        for target, i in target_lookup.items():
            group[(labels == target) & eligible] = i
        control_batches = np.flatnonzero(eligible_batch)
        batch_lookup = np.full(len(batches), -1, dtype=np.int32)
        batch_lookup[control_batches] = np.arange(len(control_batches))
        keep_nt = nt & eligible_batch[batch_codes]
        group[keep_nt] = len(targets) + batch_lookup[batch_codes[keep_nt]]
        count = np.bincount(group[group >= 0], minlength=len(targets)+len(control_batches))
        fractions = np.zeros((len(targets), len(control_batches)), np.float64)
        keep_t = (group >= 0) & (group < len(targets))
        np.add.at(fractions, (group[keep_t], batch_lookup[batch_codes[keep_t]]), 1)
        fractions /= count[:len(targets), None]
        total = np.zeros((len(count), len(cols)), np.float64)
        squared = np.zeros_like(total)
        matrix = h["X"]
        if not isinstance(matrix, h5py.Dataset):
            raise ValueError("This audited streaming path expects dense source HDF5")
        chunk = matrix.chunks[0] if matrix.chunks else 2048
        last_report = time.monotonic()
        for start in range(0, len(labels), chunk):
            end = min(len(labels), start + chunk)
            ids = np.flatnonzero(group[start:end] >= 0)
            if not len(ids):
                continue
            block = matrix[start:end][ids][:, cols].astype(np.float64)
            depth = block.sum(1)
            if (not np.isfinite(block).all() or (block < 0).any()
                    or not np.equal(block, np.floor(block)).all() or (depth <= 0).any()):
                raise ValueError("Invalid source raw counts")
            block *= 10000 / depth[:, None]
            reducer = sparse.csr_matrix((np.ones(len(ids)),
                (group[start:end][ids], np.arange(len(ids)))), shape=(len(count), len(ids)))
            total += reducer @ block
            squared += reducer @ np.square(block)
            if time.monotonic() - last_report > 30:
                print(json.dumps({"source": source, "scanned": end, "total": len(labels)}), flush=True)
                last_report = time.monotonic()
        means, var_mean = variance_of_mean(total, squared, count)
        treated = means[:len(targets)]
        control = fractions @ means[len(targets):]
        control_variance = fractions ** 2 @ var_mean[len(targets):]
        effect = np.log((treated + .1) / (control + .1))
        variance = var_mean[:len(targets)] / (treated + .1) ** 2 + control_variance / (control + .1) ** 2
        if not np.isfinite(effect).all() or not np.isfinite(variance).all():
            raise ValueError("Non-finite source effect statistics")
        np.savez(out / "statistics.npz", effects=effect.astype(np.float32),
                 variances=variance.astype(np.float32), controls=control.astype(np.float32),
                 gene_positions=dest, cells=count[:len(targets)])
        record = {"source": source, "context": CONTEXTS[source], "targets": targets,
                  "training_cells": int(count[:len(targets)].sum()), "NT_cells": int(count[len(targets):].sum()),
                  "conditions": len(targets), "measured_genes": len(cols),
                  "cells_per_condition_quantiles": np.quantile(count[:len(targets)], [0,.25,.5,.75,1]).tolist(),
                  "excluded_development_cells": len(excluded), "control_batches": len(control_batches),
                  "raw_path": str(raw_path), "raw_bytes": raw_path.stat().st_size,
                  "protocol_sha256": sha(args.previous / "protocol.json"),
                  "previous_manifest_sha256": sha(old / "manifest.json"),
                  "original_rows_sha256": sha(old / "original_rows.npy"),
                  "statistics_sha256": sha(out / "statistics.npz"),
                  "elapsed_seconds": time.monotonic()-start_time}
        save_json(out / "summary.json", record)
        print(json.dumps({k: v for k, v in record.items() if k != "targets"}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("/mnt/e/vcc2026-data"))
    parser.add_argument("--source", choices=SOURCES)
    args = parser.parse_args()
    for name in [args.source] if args.source else SOURCES:
        aggregate_source(args, name)
