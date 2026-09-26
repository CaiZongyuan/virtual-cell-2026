import json
from types import SimpleNamespace

import h5py
import numpy as np

from aggregate import aggregate_source


def test_streamed_moments_exclude_development_and_match_batch_controls(tmp_path):
    previous, root, work = [tmp_path / s for s in ["old", "raw-root", "new"]]
    prepared = previous / "prepared/gwps"
    prepared.mkdir(parents=True)
    (root / "raw").mkdir(parents=True)
    (previous / "protocol.json").write_text(json.dumps({"genes": ["A", "B"], "training_targets": ["T"]}))
    labels = ["non-targeting"] * 32 + ["T"] * 40
    batches = ["a"] * 16 + ["b"] * 16 + ["a"] * 20 + ["b"] * 20
    matrix = np.tile([10., 20., 500.], (72, 1))
    matrix[16:32, :2] = [30, 20]
    matrix[32:52, :2] = [20, 20]
    matrix[52:, :2] = [60, 20]
    dev = list(range(32, 36)) + list(range(52, 56))
    matrix[dev, :2] = [1000, 1]
    np.save(prepared / "original_rows.npy", np.arange(72))
    (prepared / "manifest.json").write_text(json.dumps({"groups": [{"target": "T", "development": dev}]}))
    with h5py.File(root / "raw/gwps.h5ad", "w") as h:
        h.create_dataset("X", data=matrix, chunks=(16, 3))
        var = h.create_group("var")
        var.create_dataset("_index", data=np.array(["A", "B", "outside"], dtype=h5py.string_dtype()))
        obs = h.create_group("obs")
        for key, values in [("gene", labels), ("batch", batches)]:
            obs.create_dataset(key, data=np.array(values, dtype=h5py.string_dtype()))
    aggregate_source(SimpleNamespace(previous=previous, root=root, work=work), "gwps")
    x = matrix[:, :2] / matrix[:, :2].sum(1, keepdims=True) * 10000
    training = np.array([r for r in range(32, 72) if r not in dev])
    control = .5 * x[:16].mean(0) + .5 * x[16:32].mean(0)
    treated = x[training].mean(0)
    with np.load(work / "sources/gwps/statistics.npz") as actual:
        np.testing.assert_allclose(actual["controls"][0], control, rtol=1e-6)
        np.testing.assert_allclose(actual["effects"][0], np.log((treated+.1)/(control+.1)), rtol=1e-6)
        expected_variance = x[training].var(0, ddof=1)/32/(treated+.1)**2
        np.testing.assert_allclose(actual["variances"][0], expected_variance, rtol=1e-6)
        assert actual["cells"].tolist() == [32]
