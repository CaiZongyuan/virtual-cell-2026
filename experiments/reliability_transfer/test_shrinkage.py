import numpy as np

from shrinkage import fit_prior, posterior_mean


def test_posterior_preserves_sign_and_identity_and_reduces_null_noise():
    rng = np.random.default_rng(49)
    truth = np.zeros(10000)
    truth[:1000] = rng.normal(0, .6, 1000)
    variance = np.full(len(truth), .2 ** 2)
    observed = truth + rng.normal(0, .2, len(truth))
    weights, report = fit_prior(observed, variance)
    prediction = posterior_mean(observed, variance, weights)
    assert np.mean((prediction-truth)**2) < .6 * np.mean((observed-truth)**2)
    assert np.all(np.abs(prediction) <= np.abs(observed) + 1e-7)
    assert np.all(prediction * observed >= 0)
    assert posterior_mean(np.zeros(10), np.ones(10), weights).sum() == 0
    assert report["log_likelihood_final"] >= report["log_likelihood_initial"]


def test_large_uncertainty_receives_more_shrinkage():
    weights = np.array([.8, 0, 0, .2, 0, 0, 0, 0])
    result = posterior_mean(np.array([.5, .5]), np.array([.001, .25]), weights)
    assert 0 <= result[1] < result[0] <= .5
