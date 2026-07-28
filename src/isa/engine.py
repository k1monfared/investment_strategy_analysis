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

def run_backtest(strategy_module, prices, fees=DEFAULT_FEES, slippage=DEFAULT_SLIPPAGE):
    entries, exits = _signals_from(strategy_module, prices)
    pf = vbt.Portfolio.from_signals(prices, entries, exits, fees=fees, slippage=slippage)
    equity = pf.value()
    if isinstance(equity, pd.DataFrame):
        equity = equity.sum(axis=1)
    equity = equity.dropna()
    returns = equity.pct_change().dropna()
    return BacktestResult(equity_curve=equity, returns=returns, metrics=_metrics(equity, returns))
