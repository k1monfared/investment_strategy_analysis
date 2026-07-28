import os
import duckdb
import pandas as pd

PRICE_COLUMNS = ["date", "open", "high", "low", "close", "adj_close", "volume"]

def price_path(ticker, root="data/prices"):
    return os.path.join(root, f"{ticker.upper()}.parquet")

def write_prices(ticker, df, root="data/prices"):
    missing = set(PRICE_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    out = df[PRICE_COLUMNS].copy()
    out["date"] = pd.to_datetime(out["date"])
    out = out.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    os.makedirs(root, exist_ok=True)
    path = price_path(ticker, root)
    out.to_parquet(path, index=False)
    return path

def read_prices(ticker, root="data/prices"):
    return pd.read_parquet(price_path(ticker, root))[PRICE_COLUMNS]

def read_universe_prices(tickers, field="adj_close", root="data/prices"):
    frames = []
    for t in tickers:
        p = price_path(t, root)
        if not os.path.exists(p):
            continue
        s = pd.read_parquet(p)[["date", field]].rename(columns={field: t})
        frames.append(s.set_index("date"))
    if not frames:
        return pd.DataFrame()
    wide = pd.concat(frames, axis=1).sort_index()
    return wide[[t for t in tickers if t in wide.columns]]
