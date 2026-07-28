import numpy as np
import pandas as pd
from arch.bootstrap import StationaryBootstrap

def _auto_block(n):
    return max(1, int(round(n ** (1 / 3))))

def _sharpe(x):
    x = np.asarray(x).ravel()
    s = x.std()
    return float(np.sqrt(252) * x.mean() / s) if s else 0.0

def bootstrap_ci(returns, metric_fn, n_reps=1000, block_size=None, alpha=0.05, seed=0):
    arr = np.asarray(returns, dtype=float)
    block = block_size or _auto_block(len(arr))
    bs = StationaryBootstrap(block, arr, seed=seed)
    stats_out = []
    for data, _ in bs.bootstrap(n_reps):
        stats_out.append(metric_fn(data[0]))
    lo = float(np.percentile(stats_out, 100 * alpha / 2))
    hi = float(np.percentile(stats_out, 100 * (1 - alpha / 2)))
    return lo, hi

def sharpe_ci(returns, **kw):
    return bootstrap_ci(returns, _sharpe, **kw)
