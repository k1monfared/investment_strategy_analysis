import numpy as np, pandas as pd
from isa import runner, prices, seed_categories as sc

def _setup(tmp_path):
    proot = str(tmp_path / "prices")
    idx = pd.date_range("2022-01-01", periods=300, freq="B")
    for t, base in [("AAPL", 100), ("MSFT", 50)]:
        trend = np.linspace(base, base * 1.5, len(idx))
        prices.write_prices(t, pd.DataFrame({
            "date": idx, "open": trend, "high": trend, "low": trend,
            "close": trend, "adj_close": trend, "volume": 100}), root=proot)
    croot = str(tmp_path / "categories")
    sc.save_categories(
        sc.build_sectors([{"ticker": "AAPL", "sector": "Technology", "industry": "x", "sic": 1},
                          {"ticker": "MSFT", "sector": "Technology", "industry": "y", "sic": 2}]),
        sc.build_membership({"sp500": ["AAPL", "MSFT"]}), root=croot)
    rroot = str(tmp_path / "results")
    return {"price_root": proot, "cat_root": croot, "theme_root": croot, "results_root": rroot}

def test_run_all_writes_results(tmp_path):
    roots = _setup(tmp_path)
    n = runner.run_all(["index:sp500", "AAPL"], "2026-07-27",
                       strategies_folder="strategies", roots=roots)
    assert n >= 2
    from isa import results
    df = results.load_results(root=roots["results_root"])
    assert not df.empty
    assert set(df["universe"]) == {"index:sp500", "AAPL"}
