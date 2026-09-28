"""Source-only effect fitting and a count decoder that can express zeros."""

from __future__ import annotations

import numpy as np

from effects import context_average


GRID = (0.0, 0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0)


def additive_effects(deltas, controls, masks):
    # Invert the recorded log((treated + 0.1)/(control + 0.1)).
    treated = np.maximum(np.exp(deltas.astype(np.float64)) * (controls + 0.1) - 0.1, 0)
    return np.where(masks, treated - controls, 0)


def aggregate(target, entries, values, masks, exclude_context=None):
    indices = [i for i, row in enumerate(entries)
               if row["target"] == target and row["context"] != exclude_context]
    if not indices:
        return np.zeros(values.shape[1]), np.zeros(values.shape[1], dtype=bool)
    return context_average(values[indices], masks[indices], [entries[i]["context"] for i in indices])


def expected_mean(control, delta, measured, alpha, mode):
    if mode == "multiplicative":
        result = control * np.exp(np.where(measured, np.clip(delta, -np.log(4), np.log(4))*alpha, 0))
    elif mode == "additive":
        result = np.maximum(control + np.where(measured, delta*alpha, 0), 0)
    else:
        raise ValueError(mode)
    total = result.sum()
    if total <= 0 or not np.isfinite(result).all():
        raise ValueError("Invalid expected mean")
    return result * (10000 / total)


def mean_shift_counts(counts, delta, measured, control_mean, alpha, rng):
    counts = np.asarray(counts)
    delta, control_mean = np.asarray(delta, dtype=np.float64), np.asarray(control_mean, dtype=np.float64)
    measured = np.asarray(measured, dtype=bool)
    if (counts.ndim != 2 or delta.shape != (counts.shape[1],)
            or control_mean.shape != delta.shape or measured.shape != delta.shape
            or not 0 <= alpha <= 1 or not np.isfinite(delta).all()
            or not np.isfinite(control_mean).all() or (control_mean < 0).any()
            or not np.isfinite(counts).all() or (counts < 0).any()
            or not np.equal(counts, np.floor(counts)).all()):
        raise ValueError("Invalid mean-shift count contract")
    depth = counts.sum(axis=1, dtype=np.float64)
    if np.any(depth <= 0) or np.any(depth > 1_000_000):
        raise ValueError("Invalid input cell depth")
    difference = np.maximum(control_mean + np.where(measured, alpha*delta, 0), 0) - control_mean
    output = counts.astype(np.int64, copy=True)
    down, up = difference < 0, difference > 0
    keep = (control_mean[down] + difference[down]) / control_mean[down]
    output[:, down] = rng.binomial(output[:, down], np.clip(keep, 0, 1))
    output[:, up] += rng.poisson(depth[:, None] / 10000 * difference[up])
    totals = output.sum(axis=1)
    if np.any(totals < 1) or np.any(totals > 1_000_000):
        raise ValueError("Decoded cell depth outside benchmark contract")
    return output.astype(np.int32)
