import pandas as pd
from isa import seed_categories as sc

def test_build_sectors_normalizes():
    df = sc.build_sectors([
        {"ticker": "aapl", "sector": "Technology", "industry": "x", "sic": 3571},
        {"ticker": "AAPL", "sector": "Technology", "industry": "x", "sic": 3571},
    ])
    assert list(df.columns) == ["ticker", "sector", "industry", "sic"]
    assert df["ticker"].tolist() == ["AAPL"]  # deduped, upper-cased

def test_build_membership_shapes():
    df = sc.build_membership({"sp500": ["AAPL", "MSFT"]})
    assert set(df.columns) == {"ticker", "index", "start", "end"}
    assert set(df["ticker"]) == {"AAPL", "MSFT"}
    assert (df["index"] == "sp500").all()

def test_save_categories_roundtrip(tmp_path):
    root = str(tmp_path)
    s = sc.build_sectors([{"ticker": "AAPL", "sector": "Technology", "industry": "x", "sic": 1}])
    m = sc.build_membership({"sp500": ["AAPL"]})
    sc.save_categories(s, m, root=root)
    from isa import universe
    assert universe.resolve_universe("sector:Technology", cat_root=root,
                                     theme_root=root, price_root=root) == ["AAPL"]
