"""Heteroskedastic normal-means posterior with a fixed normal-mixture prior."""

import numpy as np
from scipy.special import logsumexp


SCALES = np.array([0, .025, .05, .1, .2, .4, .8, 1.6], dtype=np.float64)


def responsibilities(effect, variance, weights):
    total = np.maximum(variance[:, None], 1e-8) + SCALES[None, :] ** 2
    logp = -.5 * (np.log(total) + effect[:, None] ** 2 / total)
    logp += np.log(np.maximum(weights, 1e-300))
    normalizer = logsumexp(logp, axis=1, keepdims=True)
    return np.exp(logp - normalizer), total, float(normalizer.sum())


def fit_prior(effect, variance, seed=42):
    effect, variance = np.asarray(effect).ravel(), np.asarray(variance).ravel()
    if (effect.shape != variance.shape or len(effect) == 0
            or not np.isfinite(effect).all() or not np.isfinite(variance).all()
            or (variance < 0).any()):
        raise ValueError("Invalid normal-means observations")
    if len(effect) > 200000:
        ids = np.random.default_rng(seed).choice(len(effect), 200000, replace=False)
        effect, variance = effect[ids], variance[ids]
    weights = np.ones(len(SCALES)) / len(SCALES)
    likelihoods = []
    for _ in range(100):
        probability, _, likelihood = responsibilities(effect, variance, weights)
        weights = probability.mean(0)
        weights /= weights.sum()
        likelihoods.append(likelihood)
    return weights, {"fit_observations": len(effect), "scales": SCALES.tolist(),
                     "weights": weights.tolist(), "iterations": 100,
                     "log_likelihood_initial": likelihoods[0],
                     "log_likelihood_final": likelihoods[-1]}


def posterior_mean(effect, variance, weights):
    shape = effect.shape
    flat, noise = np.asarray(effect).ravel(), np.asarray(variance).ravel()
    if (flat.shape != noise.shape or not np.isfinite(flat).all()
            or not np.isfinite(noise).all() or (noise < 0).any()):
        raise ValueError("Invalid posterior input")
    output = np.zeros(len(flat), np.float32)
    for start in range(0, len(flat), 100000):
        end = min(len(flat), start + 100000)
        probability, total, _ = responsibilities(flat[start:end], noise[start:end], weights)
        shrink = (probability * SCALES[None, :] ** 2 / total).sum(1)
        output[start:end] = flat[start:end] * shrink
    return output.reshape(shape)
