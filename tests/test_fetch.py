import pandas as pd
from isa import fetch, prices

def _raw(dates, closes):
    idx = pd.to_datetime(dates)
    return pd.DataFrame({
        "Open": closes, "High": closes, "Low": closes,
        "Close": closes, "Adj Close": closes, "Volume": [100] * len(closes),
    }, index=idx)

def test_normalize_maps_columns():
    out = fetch.normalize_ohlcv(_raw(["2024-01-02"], [5.0]))
    assert list(out.columns) == prices.PRICE_COLUMNS
    assert out.iloc[0]["adj_close"] == 5.0

def test_update_writes_all_when_empty(tmp_path):
    root = str(tmp_path)
    def fetcher(ticker, start):
        return _raw(["2024-01-02", "2024-01-03"], [10.0, 11.0])
    n = fetch.update_ticker("AAPL", fetcher, root=root)
    assert n == 2
    assert len(prices.read_prices("AAPL", root=root)) == 2

def test_update_appends_only_new(tmp_path):
    root = str(tmp_path)
    prices.write_prices("AAPL", fetch.normalize_ohlcv(
        _raw(["2024-01-02", "2024-01-03"], [10.0, 11.0])), root=root)
    def fetcher(ticker, start):
        # returns overlap + one new day
        return _raw(["2024-01-03", "2024-01-04"], [11.0, 12.0])
    n = fetch.update_ticker("AAPL", fetcher, root=root)
    assert n == 1
    df = prices.read_prices("AAPL", root=root)
    assert df["date"].tolist()[-1] == pd.Timestamp("2024-01-04")
    assert len(df) == 3
