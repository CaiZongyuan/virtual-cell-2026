"""Run the unchanged benchmark, caching immutable prediction counts as well.

Only AnnData storage changes. RowSource, moments, DE, scaling, file hashing and
validation continue to use the pinned upstream code. Backed/resident row parity
is checked before exposing the resident object to the scorer.
"""

from pathlib import Path

import h5py
import numpy as np

from score_cached_controls import open_controls
from vcc_h1_eval import cli, scorer
from vcc_h1_eval.bounded import RowSource


def cache_prediction(original, max_bytes=4 * 2**30):
    with h5py.File(original.filename) as handle:
        matrix = handle["X"]
        required = sum(matrix[k].size * matrix[k].dtype.itemsize for k in ["data", "indices", "indptr"])
    if required > max_bytes:
        raise ValueError(f"Prediction exceeds declared resident bound: {required} bytes")
    labels = original.obs["target_gene"].astype(str).to_numpy()
    rows = np.arange(original.n_obs)
    source = RowSource(original, rows, labels)
    rng = np.random.default_rng(2026)
    # Includes repeated and shuffled logical rows: catches axis/order corruption.
    positions = rng.integers(0, original.n_obs, 128)
    expected = source.read(positions)
    loaded = original.to_memory()
    actual = RowSource(loaded, rows, labels).read(positions)
    if expected.shape != actual.shape or (expected != actual).nnz:
        raise ValueError("Backed/resident prediction count or row-order mismatch")
    original.file.close()
    print(f"Cached verified prediction: {required} CSR bytes; evaluator math unchanged", flush=True)
    return loaded


if __name__ == "__main__":
    args = cli.parse_args()
    original_read = scorer.ad.read_h5ad
    prediction = Path(args.prediction).resolve()

    def read(path, *positional, **kwargs):
        value = original_read(path, *positional, **kwargs)
        return cache_prediction(value) if Path(path).resolve() == prediction else value

    scorer.ad.read_h5ad = read
    scorer.open_controls = open_controls
    cli.run(args)
