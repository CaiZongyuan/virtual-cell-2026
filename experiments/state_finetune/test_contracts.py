import json

import anndata as ad
import h5py
import numpy as np
import pytest
from scipy import sparse

from data import PreparedSource, cache_controls, csv_column, gene_names, read_rows
from export import Writer
from model import integer_counts


def test_both_csv_contracts_preserve_first_gene(tmp_path):
    h1 = tmp_path / "h1.csv"
    abc = tmp_path / "abc.csv"
    h1.write_text("SAMD11\nNOC2L\n")
    abc.write_text("gene_name\nSAMD11\nNOC2L\n")
    assert csv_column(h1) == csv_column(abc, "gene_name") == ["SAMD11", "NOC2L"]


def test_nullable_official_gene_axis(tmp_path):
    path = tmp_path / "controls.h5ad"
    with h5py.File(path, "w") as handle:
        var = handle.create_group("var")
        var.attrs["_index"] = "_index"
        index = var.create_group("_index")
        index.create_dataset("values", data=["SAMD11", "NOC2L"], dtype=h5py.string_dtype())
        index.create_dataset("mask", data=[False, False])
        assert list(gene_names(handle)) == ["SAMD11", "NOC2L"]
        index["mask"][0] = True
        with pytest.raises(ValueError, match="Missing"):
            gene_names(handle)


@pytest.mark.parametrize("sparse_input", [False, True])
def test_row_reader_preserves_order_and_duplicates(tmp_path, sparse_input):
    matrix = np.array([[1, 0, 2], [0, 3, 0], [4, 0, 5]], dtype=np.float32)
    path = tmp_path / "source.h5ad"
    ad.AnnData(sparse.csr_matrix(matrix) if sparse_input else matrix).write_h5ad(path)
    with h5py.File(path) as handle:
        np.testing.assert_array_equal(read_rows(handle, [2, 0, 2]), matrix[[2, 0, 2]])
        cached = cache_controls(handle)
        selected = cached[[2, 0, 2]]
        np.testing.assert_array_equal(selected.toarray() if sparse.issparse(selected) else selected, matrix[[2, 0, 2]])
        assert cache_controls(handle, max_bytes=1) is None


def test_count_adapter_preserves_depth_and_ignores_unsupervised_predictions():
    control = np.array([[4, 0, 6], [0, 9, 1]], dtype=np.int32)
    first = np.array([[1, 0, 2], [3, 1, 9]], dtype=np.float64)
    second = first.copy()
    second[:, 2] = 1000
    supported = np.array([True, True, False])
    actual = integer_counts(first, control, supported, np.random.default_rng(42))
    other = integer_counts(second, control, supported, np.random.default_rng(42))
    np.testing.assert_array_equal(actual, other)
    np.testing.assert_array_equal(actual.sum(axis=1), control.sum(axis=1))
    assert np.issubdtype(actual.dtype, np.integer)
    assert (actual >= 0).all()
    first[0, 0] = np.nan
    with pytest.raises(ValueError, match="Non-finite"):
        integer_counts(first, control, supported, np.random.default_rng(42))


def test_streamed_h5ad_roundtrip_and_contract(tmp_path):
    path = tmp_path / "prediction.h5ad"
    writer = Writer(path, ["SAMD11", "NOC2L", "ISG15"],
                    [{"context": "A", "target_gene": "ADNP"} for _ in range(3)])
    matrix = np.array([[1, 0, 3], [0, 2, 0], [4, 0, 5]], dtype=np.int32)
    writer.append(matrix[:1])
    writer.append(matrix[1:])
    manifest = writer.finish()
    recovered = ad.read_h5ad(path)
    assert manifest["rows"] == 3
    assert manifest["stored_entries"] == np.count_nonzero(matrix)
    assert list(recovered.var_names) == ["SAMD11", "NOC2L", "ISG15"]
    np.testing.assert_array_equal(recovered.X.toarray(), matrix)
    assert recovered.obs_names.is_unique
    assert recovered.obs["target_gene"].tolist() == ["ADNP"] * 3


def test_sampling_matches_controls_to_each_treated_cells_batch(tmp_path):
    counts = sparse.csr_matrix([[10, 3], [10, 4], [100, 3], [100, 4], [1, 8], [2, 9]], dtype=np.float32)
    sparse.save_npz(tmp_path / "counts.npz", counts)
    np.save(tmp_path / "measured.npy", np.array([True, True]))
    np.save(tmp_path / "row_batches.npy", np.array(["a", "a", "b", "b", "a", "b"]))
    (tmp_path / "manifest.json").write_text(json.dumps({
        "groups": [{"target": "ADNP", "training": [4, 5], "development": []}],
        "controls_by_batch": {"a": [0, 1], "b": [2, 3]},
    }))
    source = PreparedSource(tmp_path)
    target, controls, treated, _ = source.sample(np.random.default_rng(42))
    assert target == "ADNP"
    assert set(treated[:, 0]) == {1, 2}
    np.testing.assert_array_equal(controls[:, 0] == 10, treated[:, 0] == 1)


def test_resume_keeps_complete_conditions_and_discards_partial_tail(tmp_path):
    path = tmp_path / "partial.h5ad"
    rows = [{"target_gene": "ADNP"} for _ in range(400)] + [{"target_gene": "ACLY"} for _ in range(400)]
    contract = {"checkpoint_sha256": "fixture-model", "seed": 42}
    writer = Writer(path, ["SAMD11", "NOC2L"], rows, contract=contract)
    complete = np.tile([2, 3], (400, 1))
    writer.append(complete)
    writer.append(np.tile([8, 1], (17, 1)))
    writer.file.close()
    with pytest.raises(ValueError, match="checkpoint/seed"):
        Writer(path, ["SAMD11", "NOC2L"], rows, resume=True, contract={**contract, "seed": 43})
    resumed = Writer(path, ["SAMD11", "NOC2L"], rows, resume=True, contract=contract)
    assert resumed.row == 400
    resumed.append(np.tile([4, 5], (400, 1)))
    resumed.finish()
    recovered = ad.read_h5ad(path)
    np.testing.assert_array_equal(recovered.X[:400].toarray(), complete)
    np.testing.assert_array_equal(recovered.X[400:].toarray(), np.tile([4, 5], (400, 1)))
