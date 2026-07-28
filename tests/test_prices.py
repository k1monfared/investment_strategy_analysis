import pandas as pd
from isa import prices

def _sample(ticker_close):
    return pd.DataFrame({
        "date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
        "open": [1.0, 2.0], "high": [1.0, 2.0], "low": [1.0, 2.0],
        "close": ticker_close, "adj_close": ticker_close, "volume": [10, 20],
    })

def test_write_then_read_roundtrip(tmp_path):
    root = str(tmp_path)
    prices.write_prices("AAPL", _sample([10.0, 11.0]), root=root)
    df = prices.read_prices("AAPL", root=root)
    assert list(df.columns) == prices.PRICE_COLUMNS
    assert df["adj_close"].tolist() == [10.0, 11.0]

def test_write_dedups_and_sorts(tmp_path):
    root = str(tmp_path)
    dup = pd.DataFrame({
        "date": pd.to_datetime(["2024-01-03", "2024-01-02", "2024-01-03"]),
        "open": [9, 1, 2], "high": [9, 1, 2], "low": [9, 1, 2],
        "close": [9, 1, 2], "adj_close": [9, 1, 2], "volume": [1, 2, 3],
    })
    prices.write_prices("MSFT", dup, root=root)
    df = prices.read_prices("MSFT", root=root)
    assert df["date"].is_monotonic_increasing
    assert len(df) == 2
    assert df.iloc[-1]["adj_close"] == 2  # last dup wins

def test_read_universe_wide(tmp_path):
    root = str(tmp_path)
    prices.write_prices("AAPL", _sample([10.0, 11.0]), root=root)
    prices.write_prices("MSFT", _sample([20.0, 21.0]), root=root)
    wide = prices.read_universe_prices(["AAPL", "MSFT"], root=root)
    assert list(wide.columns) == ["AAPL", "MSFT"]
    assert wide.loc[pd.Timestamp("2024-01-03"), "MSFT"] == 21.0

def test_write_rejects_bad_columns(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        prices.write_prices("BAD", pd.DataFrame({"date": [1]}), root=str(tmp_path))
