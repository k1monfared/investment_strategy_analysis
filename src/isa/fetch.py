import os
import pandas as pd
from isa import prices

_COLMAP = {"Open": "open", "High": "high", "Low": "low",
           "Close": "close", "Adj Close": "adj_close", "Volume": "volume"}

def normalize_ohlcv(raw):
    df = raw.rename(columns=_COLMAP).copy()
    df["date"] = pd.to_datetime(df.index)
    return df.reset_index(drop=True)[prices.PRICE_COLUMNS]

def _default_fetcher(ticker, start):
    import yfinance as yf
    return yf.download(ticker, start=start, auto_adjust=False, progress=False)

def update_ticker(ticker, fetcher=_default_fetcher, root="data/prices"):
    last = None
    if os.path.exists(prices.price_path(ticker, root)):
        existing = prices.read_prices(ticker, root)
        if len(existing):
            last = existing["date"].max()
    start = (last + pd.Timedelta(days=1)).strftime("%Y-%m-%d") if last is not None else "1990-01-01"
    raw = fetcher(ticker, start)
    if raw is None or len(raw) == 0:
        return 0
    incoming = normalize_ohlcv(raw)
    if last is not None:
        incoming = incoming[incoming["date"] > last]
    if len(incoming) == 0:
        return 0
    combined = incoming
    if last is not None:
        combined = pd.concat([prices.read_prices(ticker, root), incoming], ignore_index=True)
    prices.write_prices(ticker, combined, root=root)
    return len(incoming)
