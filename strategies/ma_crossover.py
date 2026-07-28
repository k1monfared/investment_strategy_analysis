META = {
    "id": "ma_crossover",
    "name": "Moving Average Crossover",
    "kind": "signal",
    "params": {"fast": 20, "slow": 50},
    "description": "Hold when a fast moving average is above a slow moving average, exit when it drops below. A classic trend-following rule.",
    "long_description": """
The moving average crossover is a trend-following rule. It tracks two simple moving
averages of the closing price, a fast one over the last `fast` trading days and a slow
one over the last `slow` days. When the fast average rises above the slow average the
strategy reads this as an established uptrend and enters a long position. When the fast
average falls back below the slow average it reads this as the trend breaking down and
exits to cash.

Parameters:
- `fast` (default 20): window of the fast moving average in trading days. Roughly one
  month of data. A shorter fast window reacts more quickly but produces more whipsaw
  trades.
- `slow` (default 50): window of the slow moving average in trading days. Roughly ten
  weeks. A longer slow window smooths out noise but lags turning points more.

How it behaves:
- In a strong, persistent trend the rule captures the bulk of the move and sits out the
  worst of the reversals, which is why its maximum drawdown is typically much smaller
  than buy and hold.
- In a choppy, sideways market the two averages cross back and forth, generating many
  small losing trades. Transaction costs and slippage bite hardest here.
- Because it sells into weakness and buys into strength, it gives up some upside at
  bottoms and tops in exchange for avoiding the deepest declines.

Reading it against the baseline: compare its equity curve and Sharpe ratio to buy and
hold. A crossover that delivers a comparable return with a shallower drawdown is doing
its job even if its raw total return is lower.
""".strip(),
    "references": [
        "Brock, Lakonishok, and LeBaron (1992), Simple Technical Trading Rules and the Stochastic Properties of Stock Returns",
    ],
    # Optional client-side spec so the interactive explorer can reproduce the rule in
    # the browser. Kept in sync with params above.
    "client": {"type": "sma_crossover", "fast": 20, "slow": 50},
}

def generate(prices, params):
    fast = prices.rolling(params["fast"]).mean()
    slow = prices.rolling(params["slow"]).mean()
    return {"entries": fast > slow, "exits": fast < slow}
