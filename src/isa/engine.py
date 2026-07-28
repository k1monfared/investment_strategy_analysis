from dataclasses import dataclass
import numpy as np
import pandas as pd
import vectorbt as vbt

DEFAULT_FEES = 0.001
DEFAULT_SLIPPAGE = 0.0005

@dataclass
class BacktestResult:
    equity_curve: pd.Series
    returns: pd.Series
    metrics: dict

def _signals_from(strategy_module, prices):
    kind = strategy_module.META["kind"]
    params = strategy_module.META.get("params", {})
    out = strategy_module.generate(prices, params)
    if kind == "signal":
        return out["entries"].astype(bool), out["exits"].astype(bool)
    if kind in ("screen", "portfolio"):
        mask = out.get("mask")
        if mask is None:
            weights = out["weights"]
            mask = weights > 0
        entries = mask & ~mask.shift(1, fill_value=False)
        exits = ~mask & mask.shift(1, fill_value=False)
        return entries.astype(bool), exits.astype(bool)
    # benchmark: hold everything from first bar
    entries = pd.DataFrame(False, index=prices.index, columns=prices.columns)
    entries.iloc[0] = True
    exits = pd.DataFrame(False, index=prices.index, columns=prices.columns)
    return entries, exits

def _metrics(equity, returns):
    total_return = float(equity.iloc[-1] / equity.iloc[0] - 1)
    periods = max(len(returns), 1)
    years = periods / 252
    cagr = float((equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1) if years > 0 else 0.0
    std = returns.std()
    sharpe = float(np.sqrt(252) * returns.mean() / std) if std and not np.isnan(std) else 0.0
    running_max = equity.cummax()
    max_dd = float((equity / running_max - 1).min())
    win_rate = float((returns > 0).mean()) if len(returns) else 0.0
    return {"total_return": total_return, "cagr": cagr, "sharpe": sharpe,
            "max_drawdown": max_dd, "win_rate": win_rate}

def _equal_weight_level(prices):
    """An equal-weight index level for the universe, normalized to 1.0 at each
    column's own first observation and averaged across whatever columns exist on
    each date. Newly listed tickers join the average from their first traded day."""
    if isinstance(prices, pd.Series):
        prices = prices.to_frame()
    normed = {}
    for col in prices.columns:
        s = prices[col].dropna()
        if s.empty:
            continue
        normed[col] = prices[col] / s.iloc[0]
    if not normed:
        return pd.Series(dtype=float)
    level = pd.DataFrame(normed).mean(axis=1)
    return level.dropna()


def _dca_result(strategy_module, prices):
    """Dollar cost averaging: invest a fixed amount of cash every `every` trading
    days into an equal-weight index of the universe, buying more units when the
    price is low and fewer when it is high.

    The reported equity curve is money-weighted: value divided by cumulative
    contributions, scaled to 100 at the first contribution. So the curve shows the
    return earned per dollar invested, directly comparable to a lump-sum strategy's
    100-indexed curve, and all metrics are computed from it.
    """
    params = strategy_module.META.get("params", {})
    spec = strategy_module.generate(prices, params) or {}
    every = int(spec.get("every", params.get("every", 21)))
    level = _equal_weight_level(prices)
    if len(level) < 2:
        empty = pd.Series(dtype=float)
        return BacktestResult(empty, empty, _metrics(pd.Series([100.0, 100.0]), pd.Series([0.0])))
    units = 0.0
    contrib = 0.0
    ratio_vals = []
    for i, L in enumerate(level.to_numpy()):
        if i % every == 0 and L > 0:
            units += 1.0 / L      # contribute one unit of cash, buy at today's price
            contrib += 1.0
        value = units * L
        ratio_vals.append((value / contrib) * 100.0 if contrib > 0 else 100.0)
    equity = pd.Series(ratio_vals, index=level.index)
    returns = equity.pct_change().dropna()
    return BacktestResult(equity_curve=equity, returns=returns, metrics=_metrics(equity, returns))


def run_backtest(strategy_module, prices, fees=DEFAULT_FEES, slippage=DEFAULT_SLIPPAGE):
    if strategy_module.META.get("kind") == "cashflow":
        return _dca_result(strategy_module, prices)
    entries, exits = _signals_from(strategy_module, prices)
    pf = vbt.Portfolio.from_signals(prices, entries, exits, fees=fees, slippage=slippage)
    equity = pf.value()
    if isinstance(equity, pd.DataFrame):
        equity = equity.sum(axis=1)
    equity = equity.dropna()
    returns = equity.pct_change().dropna()
    return BacktestResult(equity_curve=equity, returns=returns, metrics=_metrics(equity, returns))
