"""Run unchanged H1 metrics with a bounded in-memory copy of fixed controls."""

import h5py
import numpy as np

from vcc_h1_eval import cli, scorer


original_open_controls = scorer.open_controls


def open_controls(args):
    # Retain the upstream source/hash/shape/label verification first.
    original = original_open_controls(args)
    with h5py.File(args.controls) as handle:
        matrix = handle["X"]
        storage = sum(matrix[name].size * matrix[name].dtype.itemsize for name in ["data", "indices", "indptr"])
    if storage > 4 * 2**30:
        return original
    rows = np.linspace(0, original.n_obs-1, 128, dtype=int)
    expected = original[rows].X.toarray()
    loaded = original.to_memory()
    np.testing.assert_array_equal(loaded.X[rows].toarray(), expected)
    original.file.close()
    print(f"Cached verified controls in memory: {storage:,} CSR bytes; metric implementation unchanged", flush=True)
    return loaded


if __name__ == "__main__":
    scorer.open_controls = open_controls
    cli.main()
