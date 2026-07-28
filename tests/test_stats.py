import numpy as np, pandas as pd
from isa import stats

def _returns(seed=1, n=500):
    rng = np.random.default_rng(seed)
    return pd.Series(rng.normal(0.001, 0.01, n))

def test_ci_orders_low_below_high():
    r = _returns()
    lo, hi = stats.sharpe_ci(r, n_reps=200, seed=0)
    assert lo < hi

def test_ci_brackets_point_estimate_usually():
    r = _returns()
    point = np.sqrt(252) * r.mean() / r.std()
    lo, hi = stats.sharpe_ci(r, n_reps=500, seed=0)
    assert lo <= point <= hi

def test_ci_is_deterministic_with_seed():
    r = _returns()
    assert stats.sharpe_ci(r, n_reps=200, seed=42) == stats.sharpe_ci(r, n_reps=200, seed=42)
