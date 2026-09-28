import numpy as np
import pytest

from effects import context_average, transfer_counts


def test_identity_and_unmeasured_counts_are_exact():
    counts = np.array([[1, 0, 15], [8, 9, 0]])
    np.testing.assert_array_equal(transfer_counts(counts, np.zeros(3), np.ones(3, bool),
                                                np.random.default_rng(4)), counts)
    result = transfer_counts(counts, np.array([1., -1., 9.]), np.array([1, 1, 0], bool),
                             np.random.default_rng(4))
    np.testing.assert_array_equal(result[:, 2], counts[:, 2])


def test_stochastic_decoder_matches_expected_effect():
    counts = np.tile([20, 20, 20], (100000, 1))
    result = transfer_counts(counts, np.log([0.5, 2., 1.]), np.ones(3, bool),
                             np.random.default_rng(123), shrink=1)
    np.testing.assert_allclose(result.mean(axis=0), [10, 40, 20], atol=0.1)


def test_context_average_does_not_double_weight_k562_or_missing_genes():
    value, mask = context_average([[2., 7., 0], [4., 0., 0], [8., 0., 0]],
                                  [[1, 1, 0], [1, 0, 0], [1, 0, 0]],
                                  ["K562", "K562", "RPE1"])
    np.testing.assert_allclose(value, [5.5, 7., 0.])
    np.testing.assert_array_equal(mask, [True, True, False])


@pytest.mark.parametrize("value", [np.nan, -1., 0.5])
def test_invalid_counts_rejected(value):
    with pytest.raises(ValueError):
        transfer_counts(np.array([[value, 10]]), np.zeros(2), np.ones(2, bool),
                        np.random.default_rng(4))
