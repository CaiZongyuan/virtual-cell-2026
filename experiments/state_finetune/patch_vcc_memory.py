"""Bound vcc-cli 0.1.0 prep allocations without changing checks or values."""

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import sys
import tarfile
import tempfile


def patch(audit):
    import vcc.prep
    if importlib.metadata.version("vcc-cli") != "0.1.0":
        raise ValueError("Memory patch is audited only for vcc-cli 0.1.0")
    path = Path(vcc.prep.__file__)
    original = path.read_text()
    audit.mkdir(parents=True, exist_ok=True)
    backup = audit / "vcc-prep-original.py"
    marker = "# VC2026 bounded count check"
    if marker in original:
        if not backup.exists():
            raise ValueError("Patched module has no recorded original")
        if "# VC2026 bounded row totals" in original:
            return path, backup
        prior = json.loads((audit / "vcc-memory-patch.json").read_text())
        if hashlib.sha256(original.encode()).hexdigest() != prior["patched_sha256"]:
            raise ValueError("Installed patched prep has unrecorded changes")
        original = backup.read_text()
    replacements = {
        "    frac, _ = np.modf(data)\n    return not bool(np.any(np.abs(frac) > 1e-6))":
        "    # VC2026 bounded count check: same tolerance, every stored value.\n"
        "    for start in range(0, data.size, 1_048_576):\n"
        "        frac, _ = np.modf(data[start:start + 1_048_576])\n"
        "        if np.any(np.abs(frac) > 1e-6):\n"
        "            return False\n"
        "    return True",
        "    new_x = X.astype(dtype) if issparse(X) else csr_matrix(np.asarray(X).astype(dtype))":
        "    # X is owned by this file-based prep call; reuse sparse structure.\n"
        "    if issparse(X):\n"
        "        new_x = X\n"
        "        if new_x.dtype != np.dtype(dtype):\n"
        "            new_x.data = new_x.data.astype(dtype)\n"
        "    else:\n"
        "        new_x = csr_matrix(np.asarray(X).astype(dtype))",
        "    totals = np.asarray(X.sum(axis=1)).ravel() if issparse(X) else np.asarray(X).sum(axis=1)":
        "    # VC2026 bounded row totals: avoid SciPy's full int32-to-int64 copy.\n"
        "    if issparse(X):\n"
        "        csr = X.tocsr()\n"
        "        totals = np.zeros(csr.shape[0], dtype=np.float64)\n"
        "        for row_start in range(0, csr.shape[0], 1024):\n"
        "            row_end = min(csr.shape[0], row_start + 1024)\n"
        "            ptr = csr.indptr[row_start:row_end + 1]\n"
        "            nonempty = np.diff(ptr) > 0\n"
        "            if np.any(nonempty):\n"
        "                block = csr.data[ptr[0]:ptr[-1]].astype(np.float64, copy=False)\n"
        "                starts = (ptr[:-1] - ptr[0])[nonempty]\n"
        "                totals[row_start + np.flatnonzero(nonempty)] = np.add.reduceat(block, starts)\n"
        "    else:\n"
        "        totals = np.asarray(X).sum(axis=1)",
    }
    modified = original
    for before, after in replacements.items():
        if modified.count(before) != 1:
            raise ValueError("Installed prep source differs from the audited source")
        modified = modified.replace(before, after, 1)
    compile(modified, str(path), "exec")
    backup.write_text(original)
    path.write_text(modified)
    (audit / "vcc-memory-patch.json").write_text(json.dumps({
        "package": "vcc-cli", "version": "0.1.0",
        "original_sha256": hashlib.sha256(original.encode()).hexdigest(),
        "patched_sha256": hashlib.sha256(modified.encode()).hexdigest(),
        "changes": ["chunk integer-value checks", "reuse owned CSR indices/indptr during float encoding", "bounded FP64 row totals preserving exact integer sums"],
        "validation_guards_removed": [],
    }, indent=2)+"\n")
    return path, backup


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def verify(patched_path, original_path, audit):
    import anndata as ad
    import numpy as np
    import pandas as pd
    from scipy import sparse
    import zstandard
    original = load_module("vcc_prep_original_check", original_path)
    modified = load_module("vcc_prep_bounded_check", patched_path)
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        rows = [{"context": c, "target_gene": t} for c in ["A", "B", "C"] for t in ["ADNP", "ACLY"] for _ in range(4)]
        matrix = sparse.csr_matrix(np.tile([1, 2, 4], (len(rows), 1)), dtype=np.int32)
        source = ad.AnnData(matrix, obs=pd.DataFrame(rows, index=[str(i) for i in range(len(rows))]),
                            var=pd.DataFrame(index=["SAMD11", "NOC2L", "ISG15"]))
        source.write_h5ad(root / "input.h5ad")
        (root / "genes.csv").write_text("gene_name\nSAMD11\nNOC2L\nISG15\n")
        (root / "targets.csv").write_text("target_gene\nADNP\nACLY\n")
        decoded = []
        for label, module in [("original", original), ("bounded", modified)]:
            module.run_prep(input_path=str(root/"input.h5ad"), genes_path=str(root/"genes.csv"),
                            perts_path=str(root/"targets.csv"), output_path=str(root/f"{label}.vcc"),
                            expected_gene_dim=3, cells_per_pert=4)
            with tarfile.open(root/f"{label}.vcc") as archive:
                with archive.extractfile("pred.h5ad.zst") as compressed, (root/f"{label}.h5ad").open("wb") as dest:
                    zstandard.ZstdDecompressor().copy_stream(compressed, dest)
            decoded.append(ad.read_h5ad(root/f"{label}.h5ad"))
        np.testing.assert_array_equal(decoded[0].X.toarray(), decoded[1].X.toarray())
        pd.testing.assert_frame_equal(decoded[0].obs, decoded[1].obs)
        pd.testing.assert_frame_equal(decoded[0].var, decoded[1].var)
        # Check a fractional value beyond the first chunk and at tolerance edges.
        values = np.ones(1_048_580, dtype=np.float32)
        fixture = ad.AnnData(sparse.csr_matrix(values.reshape(1, -1)))
        assert original._all_values_integer(fixture) == modified._all_values_integer(fixture)
        fixture.X.data[-1] = 1.5
        assert not original._all_values_integer(fixture)
        assert not modified._all_values_integer(fixture)
        for values, rejected in [([999_999, 1, 0], False), ([1_000_000, 1, 0], True), ([np.nan, 1, 0], True), ([0, 0, 0], True)]:
            fixture = ad.AnnData(sparse.csr_matrix([values, values]))
            fixture.obs["target_gene"] = ["ADNP", "ADNP"]
            verdicts = []
            for module in [original, modified]:
                try:
                    module.validate_matrix_values(fixture, "target_gene", 1_000_000)
                    verdicts.append(False)
                except module.PrepError:
                    verdicts.append(True)
            assert verdicts == [rejected, rejected], (values, verdicts)
    report = {"counts_equal": True, "obs_equal": True, "genes_equal": True, "fractional_tail_rejected": True,
              "row_sum_boundary_and_invalid_input_parity": True}
    (audit / "vcc-memory-patch-verification.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", type=Path, required=True)
    args = parser.parse_args()
    current, old = patch(args.audit)
    verify(current, old, args.audit)
