import pandas as pd, yaml
from isa import universe

def _seed(tmp_path):
    cat = tmp_path / "categories"; cat.mkdir()
    pd.DataFrame({"ticker": ["AAPL", "MSFT", "XOM"],
                  "sector": ["Technology", "Technology", "Energy"],
                  "industry": ["a", "b", "c"], "sic": [1, 2, 3]}
                 ).to_parquet(cat / "sectors.parquet", index=False)
    pd.DataFrame({"ticker": ["AAPL", "XOM"], "index": ["sp500", "sp500"],
                  "start": ["1990-01-01", "1990-01-01"], "end": [None, None]}
                 ).to_parquet(cat / "membership.parquet", index=False)
    th = tmp_path / "themes"; th.mkdir()
    (th / "clean.yml").write_text(yaml.safe_dump({"tickers": ["AAPL", "TSLA"]}))
    prc = tmp_path / "prices"; prc.mkdir()
    for t in ["AAPL", "MSFT", "XOM"]:
        (prc / f"{t}.parquet").write_bytes(b"")  # presence only for `all`
    return str(cat), str(th), str(prc)

def test_resolve_sector(tmp_path):
    cat, th, prc = _seed(tmp_path)
    assert sorted(universe.resolve_universe("sector:Technology", cat, th, prc)) == ["AAPL", "MSFT"]

def test_resolve_index(tmp_path):
    cat, th, prc = _seed(tmp_path)
    assert sorted(universe.resolve_universe("index:sp500", cat, th, prc)) == ["AAPL", "XOM"]

def test_resolve_theme(tmp_path):
    cat, th, prc = _seed(tmp_path)
    assert sorted(universe.resolve_universe("theme:clean", cat, th, prc)) == ["AAPL", "TSLA"]

def test_resolve_single_and_all(tmp_path):
    cat, th, prc = _seed(tmp_path)
    assert universe.resolve_universe("AAPL", cat, th, prc) == ["AAPL"]
    assert sorted(universe.resolve_universe("all", cat, th, prc)) == ["AAPL", "MSFT", "XOM"]
