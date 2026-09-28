import numpy as np
import pytest

from calibration import aggregate, mean_shift_counts


def test_excluding_k562_excludes_both_source_files():
    entries = [{"target":"A","context":c} for c in ["K562","K562","RPE1"]]
    values = np.array([[1.,2.],[3.,4.],[10.,99.]])
    masks = np.array([[1,1],[1,1],[1,0]],dtype=bool)
    mean, measured = aggregate("A",entries,values,masks)
    np.testing.assert_allclose(mean,[6,3])
    mean, measured = aggregate("A",entries,values,masks,exclude_context="K562")
    np.testing.assert_allclose(mean,[10,0])
    np.testing.assert_array_equal(measured,[True,False])


def test_null_effect_and_unmeasured_counts_are_exactly_preserved():
    counts=np.array([[1,0,9],[2,3,5],[0,1,9]])
    mu=counts.mean(0)*1000
    rng=np.random.default_rng(42)
    np.testing.assert_array_equal(mean_shift_counts(counts,np.zeros(3),np.ones(3,bool),mu,1,rng),counts)
    np.testing.assert_array_equal(mean_shift_counts(counts,np.ones(3)*100,np.ones(3,bool),mu,0,rng),counts)
    result=mean_shift_counts(counts,np.array([100,100,-1000]),np.array([1,1,0],bool),mu,.2,rng)
    np.testing.assert_array_equal(result[:,2],counts[:,2])


def test_mean_shift_creates_expression_and_matches_expected_molecule_change():
    counts=np.tile([10000,0,5],(50000,1))
    mu=counts[0]/counts[0].sum()*10000
    result=mean_shift_counts(counts,np.array([-100,100,999]),np.array([1,1,0],bool),mu,1,np.random.default_rng(991))
    assert np.all(result[:,1]>0)
    assert abs(result[:,1].mean()-100.05)<.5
    assert abs(result[:,0].mean()-9899.95)<.5
    np.testing.assert_array_equal(result[:,2],counts[:,2])


def test_empty_input_and_invalid_mean_are_rejected():
    with pytest.raises(ValueError):
        mean_shift_counts(np.zeros((2,3)),np.ones(3),np.ones(3,bool),np.ones(3),1,np.random.default_rng(0))
    with pytest.raises(ValueError):
        mean_shift_counts(np.ones((2,3)),np.ones(3),np.ones(3,bool),np.array([1,-1,2]),1,np.random.default_rng(0))
