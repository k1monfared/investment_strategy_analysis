META = {
    "id": "buy_and_hold",
    "name": "Buy and Hold",
    "kind": "benchmark",
    "params": {},
    "description": "Buy the universe on day one and hold to the end. The reference every other strategy is measured against.",
    "long_description": """
Buy and hold is the simplest possible strategy and serves as the baseline benchmark in
this project. On the first available bar it takes an equal-weight position across every
ticker in the universe and never trades again. There are no entry or exit rules, no
timing, and no parameters to tune.

Why it matters as a baseline: any active strategy has to justify its trading. Costs,
slippage, and taxes all favor doing nothing. If a rule-based strategy cannot beat buy
and hold on a risk-adjusted basis, the rule is not adding value. For that reason buy and
hold is drawn as the reference line in every strategy comparison on this dashboard.

Interpretation notes:
- On a long uptrending market the total return of buy and hold is usually hard to beat,
  but its drawdowns are also the deepest because it stays fully invested through every
  crash.
- The Sharpe ratio of buy and hold captures the market's own risk-adjusted return over
  the period, so comparing another strategy's Sharpe to this line tells you whether the
  strategy improved the return per unit of risk.
""".strip(),
    "references": [],
    "client": {"type": "buy_and_hold"},
}

def generate(prices, params):
    return {"tickers": list(prices.columns)}
