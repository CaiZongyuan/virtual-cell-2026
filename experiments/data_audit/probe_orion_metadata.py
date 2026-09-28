"""Bounded HTTP-range audit of public Orion labels; never read count columns."""

import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import urllib.request

import pyarrow
import pyarrow.parquet as pq


class BoundedRangeReader(io.RawIOBase):
    """Random access for Parquet metadata, with hard per-read and total bounds."""

    def __init__(self, url):
        self.url = url
        self.position = 0
        self.requests = 0
        self.downloaded = 0
        request = urllib.request.Request(url, headers={"Range": "bytes=-8"})
        with urllib.request.urlopen(request, timeout=45) as response:
            self.size = int(response.headers["Content-Range"].split("/")[1])
            tail = response.read(9)
        if len(tail) != 8 or tail[4:] != b"PAR1":
            raise ValueError("Range response is not a valid Parquet footer")
        self.downloaded = 8
        self.requests = 1

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        origin = {0: 0, 1: self.position, 2: self.size}[whence]
        position = origin + offset
        if not 0 <= position <= self.size:
            raise ValueError("Seek outside object")
        self.position = position
        return position

    def read(self, size=-1):
        if size < 0:
            size = self.size - self.position
        size = min(size, self.size - self.position)
        if size > 2_000_000 or self.downloaded + size > 10_000_000:
            raise ValueError("Metadata probe read budget exceeded")
        if not size:
            return b""
        start, end = self.position, self.position + size - 1
        request = urllib.request.Request(self.url, headers={"Range": f"bytes={start}-{end}"})
        with urllib.request.urlopen(request, timeout=45) as response:
            if response.headers.get("Content-Range") != f"bytes {start}-{end}/{self.size}":
                raise ValueError("Server did not honor the exact byte range")
            data = response.read(size + 1)
        if len(data) != size:
            raise ValueError("Truncated or oversized range response")
        self.requests += 1
        self.downloaded += len(data)
        self.position += len(data)
        return data


def run(args):
    protocol = json.loads(args.protocol.read_text())
    metadata = pq.read_table(args.gene_metadata).to_pydict()
    genes = metadata["gene_name"]
    tokens = metadata["gene_token_id"]
    report = {"revision": args.revision, "pyarrow_version": pyarrow.__version__,
              "gene_metadata_sha256": hashlib.sha256(args.gene_metadata.read_bytes()).hexdigest(),
              "gene_metadata_rows": len(genes), "duplicate_symbols": len(genes)-len(set(genes)),
              "duplicate_tokens": len(tokens)-len(set(tokens)),
              "official_axis_symbols_in_metadata": len(set(genes)&set(protocol["official_genes"])),
              "use": "Metadata/label feasibility audit only. No raw counts read, no training or official submission with Orion data.",
              "license": "CC BY-NC-SA 4.0, per pinned author data card; no new competition-use permission inferred",
              "batches": {}}
    for context in ["HCT116", "HEK293T"]:
        filename = f"data/{context}_Batch1.parquet"
        url = f"https://huggingface.co/datasets/Xaira-Therapeutics/X-Atlas-Orion/resolve/{args.revision}/{filename}"
        reader = BoundedRangeReader(url)
        parquet = pq.ParquetFile(reader)
        labels = parquet.read(columns=["gene_target", "guide_target", "sample", "pass_guide_filter"]).to_pydict()
        targets = Counter(labels["gene_target"])
        control_guides = [i for i, value in enumerate(labels["guide_target"]) if value and "non-targeting" in value]
        control_labels = Counter(labels["gene_target"][i] for i in control_guides)
        official = set(protocol["official_targets"])
        observed = set(targets) & official
        columns = {}
        for group in range(parquet.metadata.num_row_groups):
            row_group = parquet.metadata.row_group(group)
            for j in range(row_group.num_columns):
                column = row_group.column(j)
                columns[column.path_in_schema] = columns.get(column.path_in_schema, 0) + column.total_compressed_size
        report["batches"][context] = {"file": filename, "source_bytes": reader.size,
            "metadata_http_requests": reader.requests, "metadata_bytes_downloaded": reader.downloaded,
            "rows": parquet.metadata.num_rows, "row_groups": parquet.metadata.num_row_groups,
            "unique_target_labels_including_null": len(targets), "null_target_labels": targets[None],
            "official_targets_observed": sorted(observed), "official_target_cells": sum(targets[t] for t in observed),
            "rows_with_non_targeting_guide_text": len(control_guides),
            "gene_labels_for_non_targeting_guides": [{"gene_target": k, "cells": v} for k, v in control_labels.items()],
            "sample_labels": sorted(set(labels["sample"])),
            "guide_filter_counts": dict(Counter(map(str, labels["pass_guide_filter"]))),
            "column_compressed_bytes": columns}
        print(json.dumps({k: v for k, v in report["batches"][context].items() if k not in ["official_targets_observed", "column_compressed_bytes"]}), flush=True)
        reader.close()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--gene-metadata", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args())
