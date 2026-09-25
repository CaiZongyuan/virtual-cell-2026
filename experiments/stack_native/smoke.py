"""Pinned Stack native count/axis smoke, using NTC cells only (no H1 truth)."""

import argparse
import hashlib
import json
from pathlib import Path
import resource
import time

import anndata as ad
import h5py
import numpy as np
import pandas as pd
from scipy import sparse
import torch

from data import gene_names, h5_column, read_rows
from stack.model_loading import load_model_from_checkpoint
from stack.data.training.datasets import load_gene_list
from stack.cli.generation import _align_genes_to_target_list


EXPECTED = {
    "bc_large_aligned.ckpt": "f93cf6f42f36c8a85dc570d92e801c1fc3e1f45d55741e6bb250d178a6b6ad36",
    "basecount_1000per_15000max.pkl": "d8761dfda955b9897d3251798b72361ddd0171ef707119eaf65381bed2d85dcc",
}


def read_ntc(path, size, seed, name, already_controls=False):
    with h5py.File(path) as handle:
        genes = list(gene_names(handle))
        if already_controls:
            matrix = handle["X"]
            n = matrix.shape[0] if isinstance(matrix, h5py.Dataset) else matrix.attrs["shape"][0]
            available = np.arange(n)
        else:
            available = np.flatnonzero(h5_column(handle["obs"], "gene") == "non-targeting")
        rows = np.random.default_rng(seed).choice(available, size, replace=False)
        counts = read_rows(handle, rows)
    if len(set(genes)) != len(genes) or not np.isfinite(counts).all() or np.any(counts < 0) or not np.equal(counts, np.floor(counts)).all():
        raise ValueError("Invalid raw input")
    return ad.AnnData(sparse.csr_matrix(counts), obs=pd.DataFrame(index=[f"{name}_{i}" for i in range(size)]),
                      var=pd.DataFrame(index=genes)), rows.tolist()


def mean_proportion(matrix):
    matrix = sparse.csr_matrix(matrix)
    totals = np.asarray(matrix.sum(1)).ravel()
    if np.any(totals <= 0):
        raise ValueError("Empty model-panel cells")
    return np.asarray(matrix.multiply((1/totals)[:, None]).mean(0)).ravel()


def run(args):
    torch.set_num_threads(2)
    torch.manual_seed(42)
    np.random.seed(42)
    for name, checksum in EXPECTED.items():
        with (args.assets / name).open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != checksum:
                raise ValueError(f"Asset checksum mismatch: {name}")
    checkpoint = args.assets / "bc_large_aligned.ckpt"
    genelist = args.assets / "basecount_1000per_15000max.pkl"
    started = time.monotonic()
    model = load_model_from_checkpoint(str(checkpoint), model_class="ICL_FinetunedModel",
                                       device=torch.device("cpu"), strict=True).float().to("cuda").eval()
    native_cells = model.n_cells
    model.n_cells = 64
    genes = load_gene_list(str(genelist))
    if len(genes) != model.n_genes:
        raise ValueError("Checkpoint/gene-list width mismatch")
    h1, h1_rows = read_ntc(args.previous / "h1-benchmark/h1_controls.h5ad", 128, 42, "h1", True)
    external, source_rows = read_ntc(args.root / "raw/gwps.h5ad", 64, 43, "k562")
    query_raw = h1[64:].copy()
    query = _align_genes_to_target_list(query_raw, genes, None)
    null_proportion = mean_proportion(query.X)
    split_tv = 0.5*np.abs(mean_proportion(query.X[:32])-mean_proportion(query.X[32:])).sum()
    outputs = []
    for label, raw_base in [("same_context_ntc", h1[:64].copy()), ("cross_context_ntc", external)]:
        base = _align_genes_to_target_list(raw_base, genes, None)
        torch.manual_seed(42)
        np.random.seed(42)
        with torch.inference_mode():
            pred = model.get_incontext_prediction(base, query, str(genelist), prompt_ratio=0.25,
                    context_ratio=0.25, mode="predict", batch_size=1, num_workers=0,
                    random_seed=42, filter_organism=False)
        # Native API returns a CSR matrix in test_adata's gene order, not AnnData.
        counts = sparse.csr_matrix(pred)
        if query.var_names.tolist() != list(genes) or counts.shape != (64,len(genes)):
            raise ValueError("Unexpected output axis")
        if not np.isfinite(counts.data).all() or np.any(counts.data < 0) or not np.equal(counts.data,np.floor(counts.data)).all():
            raise ValueError("Output is not finite nonnegative integer-valued counts")
        report = {"condition":label,"shape":list(counts.shape),
                  "source_measured_model_genes":len(set(raw_base.var_names)&set(genes)),
                  "target_measured_model_genes":len(set(query_raw.var_names)&set(genes)),
                  "mean_depth_ratio":float(counts.sum()/query.X.sum()),
                  "composition_tv":float(0.5*np.abs(mean_proportion(counts)-null_proportion).sum()),
                  "ntc_split_tv":float(split_tv),"integer_finite_nonnegative":True}
        outputs.append(report)
        print(json.dumps(report),flush=True)
    report = {"checkpoint_sha256":EXPECTED[checkpoint.name],"code_revision":"cacc2e4b09435c3e536d46237d10b50f222dd144",
              "native_cells":native_cells,"diagnostic_cells":64,"precision":"FP32","batch_size":1,
              "trainable_updates":0,"parameters":sum(p.numel() for p in model.parameters()),
              "elapsed_seconds":time.monotonic()-started,"gpu_peak_bytes":torch.cuda.max_memory_allocated(),
              "host_peak_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
              "input_h1_control_rows":h1_rows,"input_gwps_control_rows":source_rows,"diagnostics":outputs,
              "scope":"NTC-only native interface/calibration smoke, not a scored optimization trial",
              "pretraining_h1_exposure":"unknown"}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--previous",type=Path,required=True)
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--assets",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    run(p.parse_args())
