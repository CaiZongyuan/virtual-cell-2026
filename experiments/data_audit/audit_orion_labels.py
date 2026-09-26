"""Audit target/control coverage across a pinned Orion file tree, labels only."""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import time

import pyarrow.parquet as pq

from probe_orion_metadata import BoundedRangeReader


def audit_file(filename, revision, panel):
    url = f"https://huggingface.co/datasets/Xaira-Therapeutics/X-Atlas-Orion/resolve/{revision}/{filename}"
    reader = BoundedRangeReader(url)
    try:
        parquet = pq.ParquetFile(reader)
        data = parquet.read(columns=["gene_target", "guide_target", "sample", "pass_guide_filter"], use_threads=False).to_pydict()
        counts, samples = Counter(), Counter()
        nt, mismatches, rejected = 0, 0, 0
        for target, guide, sample, passed in zip(data["gene_target"], data["guide_target"], data["sample"], data["pass_guide_filter"]):
            if not passed:
                rejected += 1
                continue
            is_nt_guide = bool(guide and "non-targeting" in guide)
            is_nt_label = target == "Non-Targeting"
            mismatches += is_nt_guide != is_nt_label
            samples[sample] += 1
            if is_nt_label:
                nt += 1
            elif target in panel:
                counts[target] += 1
        if mismatches or len(samples) != 1:
            raise ValueError("Control labels or file/batch identity require review")
        return {"file": filename, "context": filename.split("/")[1].split("_")[0],
                "rows": parquet.metadata.num_rows, "source_bytes": reader.size,
                "requests": reader.requests, "downloaded_bytes": reader.downloaded,
                "row_groups": parquet.metadata.num_row_groups, "sample": next(iter(samples)),
                "NT_cells": nt, "guide_filter_rejected_cells": rejected,
                "target_counts": dict(sorted(counts.items())), "status": "verified_labels_only"}
    finally:
        reader.close()


def run(args):
    tree = json.loads(args.tree.read_text())
    protocol = json.loads(args.protocol.read_text())
    if tree["sha"] != args.revision:
        raise ValueError("File tree revision differs")
    files = sorted(s["rfilename"] for s in tree["siblings"] if s["rfilename"].startswith("data/") and s["rfilename"].endswith(".parquet"))
    if len(files) != 332:
        raise ValueError("Pinned Orion file set changed")
    panel = set(protocol["training_targets"]) | set(protocol["official_targets"]) | set(protocol["h1_targets"])
    args.cache.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    records, failures = [], []
    with ThreadPoolExecutor(max_workers=2) as executor:
        jobs = {executor.submit(audit_file, filename, args.revision, panel): filename for filename in files}
        for job in as_completed(jobs):
            filename = jobs[job]
            try:
                record = job.result()
                records.append(record)
                (args.cache / (Path(filename).stem + ".json")).write_text(json.dumps(record, indent=2)+"\n")
            except Exception as error:
                failures.append({"file": filename, "type": type(error).__name__, "http_status": getattr(error, "code", None)})
            if (len(records)+len(failures)) % 10 == 0:
                print(json.dumps({"completed_files": len(records), "failed_files": len(failures),
                    "downloaded_bytes": sum(r["downloaded_bytes"] for r in records),
                    "elapsed_seconds": time.monotonic()-started}), flush=True)
    contexts = {}
    for context in ["HCT116", "HEK293T"]:
        selected = [r for r in records if r["context"] == context]
        counts = Counter()
        for record in selected:
            if record["NT_cells"] >= 16:
                counts.update(record["target_counts"])
        contexts[context] = {"verified_files": len(selected), "cells": sum(r["rows"] for r in selected),
            "NT_cells": sum(r["NT_cells"] for r in selected),
            "files_without_16_NT": [r["file"] for r in selected if r["NT_cells"] < 16],
            "official_target_counts_in_NT_matched_batches": {t: counts[t] for t in protocol["official_targets"]},
            "official_targets_at_least_32_cells": sum(counts[t] >= 32 for t in protocol["official_targets"]),
            "official_targets_at_least_64_cells": sum(counts[t] >= 64 for t in protocol["official_targets"]),
            "public_h1_target_counts_in_NT_matched_batches": {t: counts[t] for t in protocol["h1_targets"]}}
    summary = {"revision": args.revision, "complete": not failures and len(records) == len(files),
        "expected_files": len(files), "verified_files": len(records), "failures": failures,
        "http_range_requests_successful_files": sum(r["requests"] for r in records),
        "bytes_downloaded_successful_files": sum(r["downloaded_bytes"] for r in records),
        "source_bytes_successful_files": sum(r["source_bytes"] for r in records),
        "all_successful_files_have_one_row_group": all(r["row_groups"] == 1 for r in records),
        "elapsed_seconds": time.monotonic()-started, "contexts": contexts,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "Public labels only, pass_guide_filter required and batch NT counts explicit. No gene-expression/token count columns read, no training or competition submission with Orion data. Counts do not establish knockdown efficiency or count-matrix validity."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2)+"\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "contexts"}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tree", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args())
