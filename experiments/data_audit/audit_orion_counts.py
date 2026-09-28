"""Validate two pinned public count shards in small Arrow batches, without fitting."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import resource
import time

import numpy as np
import pyarrow.parquet as pq


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def run(args):
    protocol = json.loads(args.protocol.read_text())
    meta = pq.read_table(args.gene_metadata).to_pydict()
    token_ids = np.asarray(meta["gene_token_id"], dtype=np.int64)
    if len(set(token_ids)) != len(token_ids) or token_ids.min() < 0 or token_ids.max() > 1_000_000:
        raise ValueError("Unexpected gene token mapping")
    lookup = np.full(int(token_ids.max())+1, -1, np.int64)
    lookup[token_ids] = np.arange(len(token_ids))
    assets = json.loads(args.assets.read_text())
    reports = []
    for asset in assets:
        path = args.raw / Path(asset["path"]).name
        if path.stat().st_size != asset["size"] or digest(path) != asset["lfs"]["oid"]:
            raise ValueError("Pinned source checksum/size mismatch")
        started = time.monotonic()
        parquet = pq.ParquetFile(path)
        measured = np.zeros(len(token_ids), bool)
        n, entries, explicit_zeros, maximum, unsorted = 0, 0, 0, 0, 0
        total_mismatch, feature_mismatch = 0, 0
        libraries, target_counts = [], Counter()
        cols = ["gene_token_id", "gene_expression", "gene_target", "sample", "total_counts", "n_genes_by_counts"]
        for batch in parquet.iter_batches(batch_size=128, columns=cols, use_threads=False):
            tokens, counts = [batch.column(batch.schema.get_field_index(k)) for k in ["gene_token_id", "gene_expression"]]
            if tokens.null_count or counts.null_count:
                raise ValueError("Null per-cell list")
            ids = tokens.flatten().to_numpy(zero_copy_only=False)
            values = counts.flatten().to_numpy(zero_copy_only=False)
            offsets = counts.offsets.to_numpy()
            lengths = np.diff(offsets)
            offsets = offsets-offsets[0]
            if (not np.array_equal(np.diff(tokens.offsets.to_numpy()), lengths) or (lengths <= 0).any()
                    or ids.dtype.kind not in "iu" or (ids < 0).any() or (ids >= len(lookup)).any()
                    or (lookup[ids] < 0).any() or not np.isfinite(values).all() or (values < 0).any()
                    or not np.equal(values, np.floor(values)).all()):
                raise ValueError("Invalid paired gene-token/count lists")
            for low, high in zip(offsets[:-1], offsets[1:]):
                cell_ids = ids[low:high]
                if not np.all(cell_ids[1:] > cell_ids[:-1]):
                    unsorted += 1
                    if len(np.unique(cell_ids)) != len(cell_ids):
                        raise ValueError("Duplicate token within a cell")
            totals = np.add.reduceat(values.astype(np.float64), offsets[:-1])
            if (totals <= 0).any():
                raise ValueError("Empty count cell")
            libraries.extend(totals.tolist())
            measured[lookup[ids[values > 0]]] = True
            entries += len(values)
            explicit_zeros += int((values == 0).sum())
            maximum = max(maximum, int(values.max()))
            # These author QC summaries might have been computed before filtering.
            # Report discrepancies rather than silently redefining the count matrix.
            obs_total = batch.column(batch.schema.get_field_index("total_counts")).to_numpy()
            obs_features = batch.column(batch.schema.get_field_index("n_genes_by_counts")).to_numpy()
            total_mismatch += int((totals != obs_total).sum())
            nonzero_features = np.add.reduceat((values > 0).astype(np.int64), offsets[:-1])
            feature_mismatch += int((nonzero_features != obs_features).sum())
            target_counts.update(batch.column(batch.schema.get_field_index("gene_target")).to_pylist())
            n += batch.num_rows
        if n != parquet.metadata.num_rows:
            raise ValueError("Incomplete shard scan")
        nonzero_symbols = {g for g, present in zip(meta["gene_name"], measured) if present}
        report = {"file": asset["path"], "source_bytes": path.stat().st_size,
                  "sha256": asset["lfs"]["oid"], "sha256_verified": True,
                  "cells": n, "stored_values_scanned": entries,
                  "finite_nonnegative_integer_counts": True, "paired_axes_verified": True,
                  "duplicate_tokens_per_cell": 0, "unsorted_token_rows": unsorted,
                  "explicit_zeros": explicit_zeros, "maximum_count": maximum,
                  "library_size_quantiles": np.quantile(libraries, [0,.25,.5,.75,1]).tolist(),
                  "rows_differing_from_author_total_counts": total_mismatch,
                  "rows_differing_from_author_n_genes": feature_mismatch,
                  "NT_cells": target_counts["Non-Targeting"], "nonzero_gene_tokens": int(measured.sum()),
                  "official_symbols_with_nonzero_counts": len(nonzero_symbols & set(protocol["official_genes"])),
                  "official_targets_present": len(set(target_counts) & set(protocol["official_targets"])),
                  "elapsed_seconds": time.monotonic()-started,
                  "process_peak_RSS_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024}
        reports.append(report)
        print(json.dumps(report), flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"revision": args.revision,
        "gene_metadata_sha256": digest(args.gene_metadata), "shards": reports,
        "scope": "Two actual raw-count shards only; full corpus validity and model benefit are not established. No Orion data used in training or submission. Duplicate gene-symbol resolution remains separate from unique token-axis validation."}, indent=2)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--gene-metadata", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args())
