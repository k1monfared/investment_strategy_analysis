import numpy as np, pandas as pd
from isa import engine, strategy

def _prices(n=260):
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    trend = pd.Series(np.linspace(100, 200, n), index=idx)
    return pd.DataFrame({"AAPL": trend})

def test_run_backtest_returns_result_with_metrics():
    mods = {m.META["id"]: m for m in strategy.discover_strategies("strategies")}
    res = engine.run_backtest(mods["ma_crossover"], _prices())
    assert set(res.metrics) == {"total_return", "cagr", "sharpe", "max_drawdown", "win_rate"}
    assert len(res.equity_curve) == len(_prices())
    assert res.metrics["total_return"] == res.metrics["total_return"]  # not NaN

def test_benchmark_beats_zero_on_uptrend():
    mods = {m.META["id"]: m for m in strategy.discover_strategies("strategies")}
    res = engine.run_backtest(mods["buy_and_hold"], _prices())
    assert res.metrics["total_return"] > 0

def test_dca_runs_and_reports_metrics():
    mods = {m.META["id"]: m for m in strategy.discover_strategies("strategies")}
    res = engine.run_backtest(mods["dollar_cost_averaging"], _prices())
    assert set(res.metrics) == {"total_return", "cagr", "sharpe", "max_drawdown", "win_rate"}
    assert len(res.equity_curve) == len(_prices())
    # money-weighted curve starts at 100 and is finite
    assert abs(res.equity_curve.iloc[0] - 100.0) < 1e-9
    assert res.metrics["total_return"] == res.metrics["total_return"]

def test_dca_trails_lump_sum_on_steady_uptrend():
    # On a monotonic uptrend, buy-and-hold (fully invested from day one) should end
    # ahead of DCA (which adds cash gradually and misses early gains).
    mods = {m.META["id"]: m for m in strategy.discover_strategies("strategies")}
    px = _prices()
    bh = engine.run_backtest(mods["buy_and_hold"], px)
    dca = engine.run_backtest(mods["dollar_cost_averaging"], px)
    assert bh.metrics["total_return"] > dca.metrics["total_return"]
