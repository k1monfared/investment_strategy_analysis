import json
import os
import pandas as pd
from isa import results, build_site

def test_comparison_table_pivots(tmp_path):
    root = str(tmp_path)
    results.append_result("s1", "2026-07-27", "AAPL",
                          {"sharpe": 1.0, "total_return": 0.2}, {}, {}, root=root)
    df = results.load_results(root=root)
    table = build_site.comparison_table(df)
    assert "sharpe" in table.columns and "total_return" in table.columns

def test_build_site_writes_html(tmp_path):
    root = str(tmp_path / "results")
    results.append_result("s1", "2026-07-27", "AAPL",
                          {"sharpe": 1.0}, {"sharpe": (0.5, 1.5)}, {}, root=root)
    out = str(tmp_path / "site")
    path = build_site.build_site(results_root=root, out_dir=out, export_prices=False)
    assert os.path.exists(path)
    html = open(path, encoding="utf-8").read()
    assert "s1" in html
    # no emojis in output
    assert all(ord(ch) < 0x1F000 for ch in html)

def test_build_site_writes_all_pages_and_assets(tmp_path):
    root = str(tmp_path / "results")
    results.append_result("ma_crossover", "2026-07-27", "AAPL",
                          {"sharpe": 1.0}, {"sharpe": (0.5, 1.5)}, {}, root=root)
    out = str(tmp_path / "site")
    build_site.build_site(results_root=root, out_dir=out, export_prices=False)
    for rel in ["index.html", "strategies.html", "explorer.html",
                "assets/style.css", "assets/explorer.js", "assets/plotly.min.js",
                "strategy/ma_crossover.html", "strategy/buy_and_hold.html"]:
        assert os.path.exists(os.path.join(out, rel)), rel
    # strategy index links to detail pages
    idx = open(os.path.join(out, "strategies.html"), encoding="utf-8").read()
    assert "strategy/ma_crossover.html" in idx
    # detail page carries the long description
    detail = open(os.path.join(out, "strategy", "ma_crossover.html"), encoding="utf-8").read()
    assert "trend-following" in detail
    # pages load Plotly from the self-hosted asset, not a CDN
    home = open(os.path.join(out, "index.html"), encoding="utf-8").read()
    assert "assets/plotly.min.js" in home
    assert "cdn.plot.ly" not in home

def test_export_data_writes_manifest_and_prices(tmp_path):
    # a tiny fake price store and category file
    price_root = tmp_path / "prices"; price_root.mkdir()
    cat_root = tmp_path / "categories"; cat_root.mkdir()
    for tk, sec in [("AAA", "Technology"), ("BBB", "Energy")]:
        pd.DataFrame({
            "date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
            "open": [1.0, 2.0], "high": [1.0, 2.0], "low": [1.0, 2.0],
            "close": [1.0, 2.0], "adj_close": [10.0, 11.0], "volume": [1, 2],
        }).to_parquet(price_root / f"{tk}.parquet", index=False)
    pd.DataFrame({"ticker": ["AAA", "BBB"], "sector": ["Technology", "Energy"],
                  "industry": ["x", "y"], "sic": [1, 2]}).to_parquet(
        cat_root / "sectors.parquet", index=False)
    out = str(tmp_path / "site")
    build_site.build_site(results_root=str(tmp_path / "results"), out_dir=out,
                          price_root=str(price_root), cat_root=str(cat_root),
                          export_prices=True)
    manifest = json.load(open(os.path.join(out, "data", "manifest.json")))
    tickers = {t["t"]: t["s"] for t in manifest["tickers"]}
    assert tickers == {"AAA": "Technology", "BBB": "Energy"}
    series = json.load(open(os.path.join(out, "data", "prices", "AAA.json")))
    assert series["c"] == [10.0, 11.0]
    strat = json.load(open(os.path.join(out, "data", "strategies.json")))
    assert any(s["id"] == "buy_and_hold" for s in strat)
