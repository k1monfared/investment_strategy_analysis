META = {
    "id": "dollar_cost_averaging",
    "name": "Dollar Cost Averaging",
    "kind": "cashflow",
    "params": {"every": 21},
    "description": "Invest a fixed amount of cash at regular intervals, buying more units when prices are low and fewer when they are high.",
    "long_description": """
Dollar cost averaging (DCA) is an investment strategy that invests a fixed amount of
money at regular intervals, regardless of the price at the time. The term was coined by
Benjamin Graham in his 1949 book The Intelligent Investor. Rather than deciding when to
buy, the investor commits to a schedule: the same number of dollars each period, month
after month or, as modeled here, every `every` trading days.

The mechanism is simple. Because a fixed dollar amount buys a variable number of shares,
the schedule automatically buys more shares when the price is low and fewer when the
price is high. Over time this tends to produce a lower average cost per share than
buying a fixed number of shares each period. Mathematically, the effective average
purchase price is the harmonic mean of the prices paid, which is always less than or
equal to the arithmetic mean.

Parameters:
- `every` (default 21): the number of trading days between contributions. 21 is roughly
  one calendar month. A smaller value contributes more often, a larger value less often.
  In markets with per-trade costs, contributing too frequently can let transaction costs
  outweigh the benefit of being invested slightly earlier.

How it behaves and how it is measured here:
- Each contribution buys into an equal-weight index of the selected universe at that
  day's price. The equity curve reported is money-weighted: the portfolio value divided
  by the total cash contributed so far, indexed to 100 at the first contribution. This
  shows the return earned per dollar invested, so it sits on the same 100-based scale as
  the lump-sum strategies and can be compared directly.
- Because capital is added gradually rather than all at once, DCA carries less exposure
  early on. In a steadily rising market a lump-sum buy and hold usually ends ahead,
  since the money that DCA holds back misses early gains. In a volatile or initially
  falling market, DCA can come out ahead by accumulating cheaper shares.

Important caveat from the literature: DCA as defined by Graham (investing income as it
arrives) is distinct from the common but different practice of taking a lump sum already
in hand and spreading it out over time. Vanguard and several academic studies show that
spreading out a lump sum is usually sub-optimal versus investing it immediately, because
markets trend up over time. The value of DCA is mostly behavioral and practical: it
enforces discipline and removes the need to time the market.
""".strip(),
    "references": [
        "Benjamin Graham (1949), The Intelligent Investor",
        "Vanguard (2012), Dollar-cost averaging just means taking risk later",
        "Wikipedia, Dollar cost averaging, https://en.wikipedia.org/wiki/Dollar_cost_averaging",
    ],
    # The browser Explorer/Overview reproduce DCA with a cashflow engine that
    # contributes a fixed amount every `every` bars into the portfolio index.
    "client": {"type": "dca", "every": 21},
}

def generate(prices, params):
    # The engine handles the cashflow simulation; expose the contribution interval.
    return {"every": int(params.get("every", 21))}
