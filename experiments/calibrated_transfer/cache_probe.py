"""Real RowSource performance regression probe on a bounded H1 fixture."""

import argparse
import json
from pathlib import Path
import time

import anndata as ad
import numpy as np

from score_cached_inputs import cache_prediction
from vcc_h1_eval.bounded import RowSource


def run(path, cached):
    original = ad.read_h5ad(path, backed="r")
    memory = original.to_memory()
    candidate = cache_prediction(original) if cached else original
    labels = memory.obs["target_gene"].astype(str).to_numpy()
    rows = np.arange(memory.n_obs)
    source = RowSource(candidate, rows, labels)
    reference = RowSource(memory, rows, labels)
    rng = np.random.default_rng(2026)
    positions = [rng.integers(0, len(rows), 256) for _ in range(4)]
    durations = {"candidate": [], "memory": []}
    for _ in range(3):
        for name, reader in [("candidate", source), ("memory", reference)]:
            start = time.perf_counter()
            output = [reader.read(indices) for indices in positions]
            durations[name].append(time.perf_counter()-start)
            if name == "candidate":
                expected = output
            else:
                for x, y in zip(expected, output):
                    assert x.shape == y.shape and (x != y).nnz == 0
    seconds = {key: float(np.median(value)) for key, value in durations.items()}
    ratio = seconds["candidate"]/seconds["memory"]
    report = {"cached": cached, "seconds": seconds, "ratio": ratio, "counts_and_order_equal": True}
    print(json.dumps(report), flush=True)
    assert ratio < 2.5, "Repeated disk-backed reads exceed 2.5x resident read time"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--cached", action="store_true")
    args = parser.parse_args()
    run(args.fixture, args.cached)
