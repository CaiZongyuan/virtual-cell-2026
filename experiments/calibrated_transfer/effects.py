"""Batch-matched effect targets and an identity-preserving raw-count decoder."""

from __future__ import annotations

import numpy as np
from scipy import sparse


def cp10k(matrix):
    totals = np.asarray(matrix.sum(axis=1)).ravel().astype(np.float64)
    if np.any(totals <= 0):
        raise ValueError("Empty cells")
    if sparse.issparse(matrix):
        return matrix.multiply((10000.0 / totals)[:, None]).tocsr()
    return np.asarray(matrix) * (10000.0 / totals[:, None])


def matched_means(source, group, split="training"):
    """Use each treatment batch's actual fraction, not a pooled NTC average."""
    rows = np.asarray(group[split])
    treated = np.asarray(cp10k(source.counts[rows]).mean(axis=0)).ravel()
    control = np.zeros(source.counts.shape[1], dtype=np.float64)
    if not hasattr(source, "_control_means"):
        source._control_means = {}
    batches, frequencies = np.unique(source.row_batches[rows], return_counts=True)
    for batch, count in zip(batches, frequencies):
        if str(batch) not in source._control_means:
            controls = source.counts[source.controls_by_batch[str(batch)]]
            source._control_means[str(batch)] = np.asarray(cp10k(controls).mean(axis=0)).ravel()
        control += count / len(rows) * source._control_means[str(batch)]
    return control, treated


def log_effect(control, treated, measured, pseudocount=0.1):
    delta = np.log((treated + pseudocount) / (control + pseudocount))
    return np.where(measured, delta, 0).astype(np.float32)


def context_average(effects, masks, contexts):
    """Avoid counting two K562 files as two independent biological contexts."""
    effects, masks = np.asarray(effects), np.asarray(masks, dtype=bool)
    sums = np.zeros(effects.shape[1], dtype=np.float64)
    counts = np.zeros_like(sums)
    contexts = np.asarray(contexts)
    for context in np.unique(contexts):
        rows = contexts == context
        count = masks[rows].sum(axis=0)
        mean = np.divide((effects[rows] * masks[rows]).sum(axis=0), count,
                         out=np.zeros_like(sums), where=count > 0)
        sums += mean
        counts += count > 0
    return np.divide(sums, counts, out=np.zeros_like(sums), where=counts > 0), counts > 0


def transfer_counts(counts, delta, measured, rng, shrink=0.5):
    """Binomial thinning / Poisson additions, with no global renormalization."""
    counts = np.asarray(counts)
    delta = np.asarray(delta, dtype=np.float64)
    measured = np.asarray(measured, dtype=bool)
    if (counts.ndim != 2 or delta.shape != (counts.shape[1],)
            or measured.shape != delta.shape or not np.isfinite(delta).all()
            or not np.isfinite(counts).all() or (counts < 0).any()
            or not np.equal(counts, np.floor(counts)).all()
            or not 0 <= shrink <= 1):
        raise ValueError("Invalid count/effect contract")
    output = counts.astype(np.int64, copy=True)
    factors = np.exp(np.where(measured, np.clip(delta, -np.log(4), np.log(4)) * shrink, 0))
    down, up = factors < 1, factors > 1
    output[:, down] = rng.binomial(output[:, down], factors[down])
    output[:, up] += rng.poisson(output[:, up] * (factors[up] - 1))
    totals = output.sum(axis=1)
    if np.any(totals < 1) or np.any(totals > 1_000_000):
        raise ValueError("Decoded cell depth outside benchmark contract")
    return output.astype(np.int32)
