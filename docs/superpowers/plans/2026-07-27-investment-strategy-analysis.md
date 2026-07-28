# Investment Strategy Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a GitHub-hosted system to define investment strategies, backtest them across US stocks/ETFs with confidence intervals, and publish an auto-growing static comparison dashboard.

**Architecture:** Thin glue over mature FOSS. Per-ticker Parquet price files queried by DuckDB, a strategy interface that emits signals executed by vectorbt, results appended to a Parquet store, and a static Plotly dashboard. GitHub Actions runs updates on a schedule and deploys the site to GitHub Pages.

**Tech Stack:** Python, yfinance, pandas, pyarrow, duckdb, vectorbt, quantstats, empyrical-reloaded, arch, plotly, pyyaml, pytest.

## Global Constraints

- Python version floor: 3.11
- FOSS only: all runtime dependencies must be permissively licensed (Apache/MIT/BSD); vectorbt OSS Commons Clause is accepted because the project is never sold
- Price data: one Parquet file per ticker under `data/prices/`, schema `date, open, high, low, close, adj_close, volume`; files are independent and manually addable; queried via DuckDB glob
- Price files are git-LFS tracked; category/results/theme files are committed as plain files
- Documentation authored in loglog format (`*.log`), converted to markdown when needed
- Visualization: bar charts always start at zero; use line/dot/slope charts to emphasize change; no emojis anywhere in web UI or HTML
- Writing style in docs: no em/en dashes or semicolons; use commas, colons, periods
- Everything runnable locally via the same entry scripts the GitHub Actions workflow calls; nothing is Actions-only

---

### Task 1: Project scaffolding and dependencies

**Files:**
- Create: `pyproject.toml`
- Create: `src/isa/__init__.py`
- Create: `tests/__init__.py`
- Create: `.gitattributes`
- Create: `requirements.txt`
- Test: `tests/test_smoke.py`

**Interfaces:**
- Consumes: nothing
- Produces: importable package `isa` (version string `isa.__version__`); installed dev tooling `pytest`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_smoke.py
import isa

def test_package_has_version():
    assert isinstance(isa.__version__, str)
    assert isa.__version__
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_smoke.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'isa'`

- [ ] **Step 3: Create package and config**

```python
# src/isa/__init__.py
__version__ = "0.1.0"
```

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "isa"
version = "0.1.0"
requires-python = ">=3.11"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

```
# requirements.txt
yfinance
pandas
pyarrow
duckdb
vectorbt
quantstats
empyrical-reloaded
arch
plotly
pyyaml
pytest
```

```
# .gitattributes
data/prices/*.parquet filter=lfs diff=lfs merge=lfs -text
```

Create empty `tests/__init__.py`.

- [ ] **Step 4: Install and run tests**

Run: `pip install -r requirements.txt && pip install -e . && python -m pytest tests/test_smoke.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml requirements.txt .gitattributes src/isa/__init__.py tests/__init__.py tests/test_smoke.py
git commit -m "chore: scaffold isa package with deps and LFS config"
```

---

### Task 2: Price store reader/writer (per-ticker Parquet)

**Files:**
- Create: `src/isa/prices.py`
- Test: `tests/test_prices.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `PRICE_COLUMNS = ["date", "open", "high", "low", "close", "adj_close", "volume"]`
  - `price_path(ticker: str, root: str = "data/prices") -> str`
  - `write_prices(ticker: str, df: pandas.DataFrame, root: str = "data/prices") -> str` (validates columns, sorts by date, dedups on date keeping last, writes Parquet, returns path)
  - `read_prices(ticker: str, root: str = "data/prices") -> pandas.DataFrame`
  - `read_universe_prices(tickers: list[str], field: str = "adj_close", root: str = "data/prices") -> pandas.DataFrame` (wide frame: index=date, columns=ticker, values=field, via DuckDB glob)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_prices.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_prices.py -v`
Expected: FAIL with `ModuleNotFoundError` / `AttributeError` on `isa.prices`

- [ ] **Step 3: Write minimal implementation**

```python
# src/isa/prices.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_prices.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/isa/prices.py tests/test_prices.py
git commit -m "feat: per-ticker parquet price store with duckdb universe reader"
```

---

### Task 3: Price fetching and incremental update

**Files:**
- Create: `src/isa/fetch.py`
- Test: `tests/test_fetch.py`

**Interfaces:**
- Consumes: `isa.prices.read_prices`, `isa.prices.write_prices`, `isa.prices.price_path`, `isa.prices.PRICE_COLUMNS`
- Produces:
  - `normalize_ohlcv(raw: pandas.DataFrame) -> pandas.DataFrame` (maps a yfinance-style frame with a DatetimeIndex and columns Open/High/Low/Close/Adj Close/Volume into `PRICE_COLUMNS`)
  - `update_ticker(ticker: str, fetcher, root: str = "data/prices") -> int` (fetches, appends only rows newer than the last stored date, returns count of new rows; `fetcher(ticker, start) -> raw df` is injected so tests avoid network)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_fetch.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_fetch.py -v`
Expected: FAIL with `ModuleNotFoundError` on `isa.fetch`

- [ ] **Step 3: Write minimal implementation**

```python
# src/isa/fetch.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_fetch.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/isa/fetch.py tests/test_fetch.py
git commit -m "feat: incremental per-ticker price fetch/update with injectable fetcher"
```

---

### Task 4: Categorization store (sectors, membership, themes, universe resolution)

**Files:**
- Create: `src/isa/universe.py`
- Create: `data/themes/example_tech.yml`
- Test: `tests/test_universe.py`

**Interfaces:**
- Consumes: nothing (reads category/theme files directly)
- Produces:
  - `load_sectors(root: str = "data/categories") -> pandas.DataFrame` (columns `ticker, sector, industry, sic`)
  - `load_membership(root: str = "data/categories") -> pandas.DataFrame` (columns `ticker, index, start, end`)
  - `load_theme(name: str, root: str = "data/themes") -> list[str]`
  - `resolve_universe(spec: str, cat_root="data/categories", theme_root="data/themes", price_root="data/prices") -> list[str]` handling: `all`, `TICKER`, `sector:<name>`, `index:<name>`, `theme:<name>`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_universe.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_universe.py -v`
Expected: FAIL with `ModuleNotFoundError` on `isa.universe`

- [ ] **Step 3: Write minimal implementation**

```python
# src/isa/universe.py
import os, glob
import pandas as pd
import yaml

def load_sectors(root="data/categories"):
    return pd.read_parquet(os.path.join(root, "sectors.parquet"))

def load_membership(root="data/categories"):
    return pd.read_parquet(os.path.join(root, "membership.parquet"))

def load_theme(name, root="data/themes"):
    with open(os.path.join(root, f"{name}.yml")) as f:
        return list(yaml.safe_load(f)["tickers"])

def resolve_universe(spec, cat_root="data/categories", theme_root="data/themes", price_root="data/prices"):
    if spec == "all":
        return sorted(os.path.splitext(os.path.basename(p))[0]
                      for p in glob.glob(os.path.join(price_root, "*.parquet")))
    if spec.startswith("sector:"):
        name = spec.split(":", 1)[1]
        df = load_sectors(cat_root)
        return df.loc[df["sector"] == name, "ticker"].tolist()
    if spec.startswith("index:"):
        name = spec.split(":", 1)[1]
        df = load_membership(cat_root)
        return df.loc[df["index"] == name, "ticker"].tolist()
    if spec.startswith("theme:"):
        return load_theme(spec.split(":", 1)[1], theme_root)
    return [spec.upper()]
```

```yaml
# data/themes/example_tech.yml
tickers:
  - AAPL
  - MSFT
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_universe.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/isa/universe.py data/themes/example_tech.yml tests/test_universe.py
git commit -m "feat: universe resolution over sectors, index membership, themes"
```

---

### Task 5: Category data seeding script (SEC + yfinance + Wikipedia)

**Files:**
- Create: `src/isa/seed_categories.py`
- Test: `tests/test_seed_categories.py`

**Interfaces:**
- Consumes: `isa.universe.load_sectors` (for schema alignment only)
- Produces:
  - `build_sectors(rows: list[dict]) -> pandas.DataFrame` (normalizes to columns `ticker, sector, industry, sic`, upper-cases ticker, dedups on ticker keeping last)
  - `build_membership(constituents: dict[str, list[str]]) -> pandas.DataFrame` (maps `{index_name: [tickers]}` to columns `ticker, index, start, end` with `start="1990-01-01"`, `end=None`)
  - `save_categories(sectors_df, membership_df, root="data/categories") -> None`
  - a `main()` CLI guard that wires real sources but is NOT executed in tests

- [ ] **Step 1: Write the failing test**

```python
# tests/test_seed_categories.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_seed_categories.py -v`
Expected: FAIL with `ModuleNotFoundError` on `isa.seed_categories`

- [ ] **Step 3: Write minimal implementation**

```python
# src/isa/seed_categories.py
import os
import pandas as pd

SECTOR_COLUMNS = ["ticker", "sector", "industry", "sic"]

def build_sectors(rows):
    df = pd.DataFrame(rows, columns=SECTOR_COLUMNS)
    df["ticker"] = df["ticker"].str.upper()
    return df.drop_duplicates("ticker", keep="last").reset_index(drop=True)

def build_membership(constituents):
    out = []
    for index_name, tickers in constituents.items():
        for t in tickers:
            out.append({"ticker": t.upper(), "index": index_name,
                        "start": "1990-01-01", "end": None})
    return pd.DataFrame(out, columns=["ticker", "index", "start", "end"])

def save_categories(sectors_df, membership_df, root="data/categories"):
    os.makedirs(root, exist_ok=True)
    sectors_df.to_parquet(os.path.join(root, "sectors.parquet"), index=False)
    membership_df.to_parquet(os.path.join(root, "membership.parquet"), index=False)

def _sp500_from_wikipedia():
    tables = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    t = tables[0]
    return [{"ticker": r["Symbol"], "sector": r["GICS Sector"],
             "industry": r["GICS Sub-Industry"], "sic": None}
            for _, r in t.iterrows()]

def main():
    rows = _sp500_from_wikipedia()
    sectors = build_sectors(rows)
    membership = build_membership({"sp500": sectors["ticker"].tolist()})
    save_categories(sectors, membership)
    print(f"seeded {len(sectors)} tickers")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_seed_categories.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/isa/seed_categories.py tests/test_seed_categories.py
git commit -m "feat: category seeding from wikipedia sp500 with testable builders"
```

---

### Task 6: Strategy interface and discovery

**Files:**
- Create: `src/isa/strategy.py`
- Create: `strategies/__init__.py`
- Create: `strategies/ma_crossover.py`
- Create: `strategies/buy_and_hold.py`
- Test: `tests/test_strategy.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `REQUIRED_META = {"id", "name", "kind", "params"}` and `VALID_KINDS = {"signal", "portfolio", "screen", "benchmark"}`
  - `load_strategy(path: str) -> module` (imports a file, validates it has `META` dict with required keys and a valid `kind`, and a callable `generate`)
  - `discover_strategies(folder: str = "strategies") -> list[module]` (loads every `*.py` except dunder files, sorted by `META['id']`)
  - Each strategy module exposes `META: dict` and `generate(prices: pandas.DataFrame, params: dict) -> dict`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_strategy.py
import pandas as pd
from isa import strategy

def test_discovers_shipped_strategies():
    mods = strategy.discover_strategies("strategies")
    ids = {m.META["id"] for m in mods}
    assert {"ma_crossover", "buy_and_hold"} <= ids

def test_load_validates_meta(tmp_path):
    import pytest
    bad = tmp_path / "bad.py"
    bad.write_text("META = {'id': 'x'}\n")  # missing keys, no generate
    with pytest.raises(ValueError):
        strategy.load_strategy(str(bad))

def test_ma_crossover_generate_shape():
    mods = {m.META["id"]: m for m in strategy.discover_strategies("strategies")}
    px = pd.DataFrame({"AAPL": [1, 2, 3, 4, 5, 6]}, dtype=float)
    out = mods["ma_crossover"].generate(px, {"fast": 2, "slow": 3})
    assert set(out) == {"entries", "exits"}
    assert out["entries"].shape == px.shape

def test_buy_and_hold_kind():
    mods = {m.META["id"]: m for m in strategy.discover_strategies("strategies")}
    assert mods["buy_and_hold"].META["kind"] == "benchmark"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_strategy.py -v`
Expected: FAIL with `ModuleNotFoundError` on `isa.strategy`

- [ ] **Step 3: Write minimal implementation**

```python
# src/isa/strategy.py
import glob, importlib.util, os

REQUIRED_META = {"id", "name", "kind", "params"}
VALID_KINDS = {"signal", "portfolio", "screen", "benchmark"}

def load_strategy(path):
    spec = importlib.util.spec_from_file_location(
        f"isa_strategy_{os.path.splitext(os.path.basename(path))[0]}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    meta = getattr(mod, "META", None)
    if not isinstance(meta, dict) or not REQUIRED_META <= set(meta):
        raise ValueError(f"{path}: META must be a dict with keys {sorted(REQUIRED_META)}")
    if meta["kind"] not in VALID_KINDS:
        raise ValueError(f"{path}: invalid kind {meta['kind']!r}")
    if not callable(getattr(mod, "generate", None)):
        raise ValueError(f"{path}: missing callable generate()")
    return mod

def discover_strategies(folder="strategies"):
    mods = []
    for p in sorted(glob.glob(os.path.join(folder, "*.py"))):
        if os.path.basename(p).startswith("__"):
            continue
        mods.append(load_strategy(p))
    return sorted(mods, key=lambda m: m.META["id"])
```

```python
# strategies/ma_crossover.py
META = {"id": "ma_crossover", "name": "Moving Average Crossover",
        "kind": "signal", "params": {"fast": 20, "slow": 50}}

def generate(prices, params):
    fast = prices.rolling(params["fast"]).mean()
    slow = prices.rolling(params["slow"]).mean()
    return {"entries": fast > slow, "exits": fast < slow}
```

```python
# strategies/buy_and_hold.py
META = {"id": "buy_and_hold", "name": "Buy and Hold",
        "kind": "benchmark", "params": {}}

def generate(prices, params):
    return {"tickers": list(prices.columns)}
```

Create empty `strategies/__init__.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_strategy.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/isa/strategy.py strategies/__init__.py strategies/ma_crossover.py strategies/buy_and_hold.py tests/test_strategy.py
git commit -m "feat: strategy META interface with auto-discovery and two example strategies"
```

---

### Task 7: Backtest engine (vectorbt) with metrics

**Files:**
- Create: `src/isa/engine.py`
- Test: `tests/test_engine.py`

**Interfaces:**
- Consumes: strategy modules' `generate()` output and `META["kind"]`; `isa.prices.read_universe_prices`
- Produces:
  - `DEFAULT_FEES = 0.001`, `DEFAULT_SLIPPAGE = 0.0005`
  - `run_backtest(strategy_module, prices: pandas.DataFrame, fees=DEFAULT_FEES, slippage=DEFAULT_SLIPPAGE) -> BacktestResult`
  - `BacktestResult` dataclass: `equity_curve: pandas.Series`, `returns: pandas.Series`, `metrics: dict` (keys `total_return, cagr, sharpe, max_drawdown, win_rate`)
  - metrics computed with empyrical where available, else explicit formulas

- [ ] **Step 1: Write the failing test**

```python
# tests/test_engine.py
import numpy as np, pandas as pd
from isa import engine, strategy

def _prices(n=260):
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    trend = pd.Series(np.linspace(100, 200, n), index=idx)
    return pd.DataFrame({"AAPL": trend})

def test_run_backtest_returns_result_with_metrics():
    mods = {m.META["id"]: m for m in strategy.discover_strategies("strategies")}
    res = engine.run_backtest(mods["ma_crossover"], _prices())
    assert set(res.metrics) == {"total_return", "cagr", "sharpe", "max_drawdown", "win_rate"}
    assert len(res.equity_curve) == len(_prices())
    assert res.metrics["total_return"] == res.metrics["total_return"]  # not NaN

def test_benchmark_beats_zero_on_uptrend():
    mods = {m.META["id"]: m for m in strategy.discover_strategies("strategies")}
    res = engine.run_backtest(mods["buy_and_hold"], _prices())
    assert res.metrics["total_return"] > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_engine.py -v`
Expected: FAIL with `ModuleNotFoundError` on `isa.engine`

- [ ] **Step 3: Write minimal implementation**

```python
# src/isa/engine.py
from dataclasses import dataclass
import numpy as np
import pandas as pd
import vectorbt as vbt

DEFAULT_FEES = 0.001
DEFAULT_SLIPPAGE = 0.0005

@dataclass
class BacktestResult:
    equity_curve: pd.Series
    returns: pd.Series
    metrics: dict

def _signals_from(strategy_module, prices):
    kind = strategy_module.META["kind"]
    params = strategy_module.META.get("params", {})
    out = strategy_module.generate(prices, params)
    if kind == "signal":
        return out["entries"].astype(bool), out["exits"].astype(bool)
    if kind in ("screen", "portfolio"):
        mask = out.get("mask")
        if mask is None:
            weights = out["weights"]
            mask = weights > 0
        entries = mask & ~mask.shift(1, fill_value=False)
        exits = ~mask & mask.shift(1, fill_value=False)
        return entries.astype(bool), exits.astype(bool)
    # benchmark: hold everything from first bar
    entries = pd.DataFrame(False, index=prices.index, columns=prices.columns)
    entries.iloc[0] = True
    exits = pd.DataFrame(False, index=prices.index, columns=prices.columns)
    return entries, exits

def _metrics(equity, returns):
    total_return = float(equity.iloc[-1] / equity.iloc[0] - 1)
    periods = max(len(returns), 1)
    years = periods / 252
    cagr = float((equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1) if years > 0 else 0.0
    std = returns.std()
    sharpe = float(np.sqrt(252) * returns.mean() / std) if std and not np.isnan(std) else 0.0
    running_max = equity.cummax()
    max_dd = float((equity / running_max - 1).min())
    win_rate = float((returns > 0).mean()) if len(returns) else 0.0
    return {"total_return": total_return, "cagr": cagr, "sharpe": sharpe,
            "max_drawdown": max_dd, "win_rate": win_rate}

def run_backtest(strategy_module, prices, fees=DEFAULT_FEES, slippage=DEFAULT_SLIPPAGE):
    entries, exits = _signals_from(strategy_module, prices)
    pf = vbt.Portfolio.from_signals(prices, entries, exits, fees=fees, slippage=slippage)
    equity = pf.value()
    if isinstance(equity, pd.DataFrame):
        equity = equity.sum(axis=1)
    equity = equity.dropna()
    returns = equity.pct_change().dropna()
    return BacktestResult(equity_curve=equity, returns=returns, metrics=_metrics(equity, returns))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_engine.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add src/isa/engine.py tests/test_engine.py
git commit -m "feat: vectorbt backtest engine with core performance metrics"
```

---

### Task 8: Confidence intervals via stationary bootstrap

**Files:**
- Create: `src/isa/stats.py`
- Test: `tests/test_stats.py`

**Interfaces:**
- Consumes: a returns `pandas.Series` from `isa.engine.BacktestResult`
- Produces:
  - `bootstrap_ci(returns: pandas.Series, metric_fn, n_reps=1000, block_size=None, alpha=0.05, seed=0) -> tuple[float, float]` (stationary block bootstrap CI for a scalar metric)
  - `sharpe_ci(returns, **kw) -> tuple[float, float]` convenience wrapper

- [ ] **Step 1: Write the failing test**

```python
# tests/test_stats.py
import numpy as np, pandas as pd
from isa import stats

def _returns(seed=1, n=500):
    rng = np.random.default_rng(seed)
    return pd.Series(rng.normal(0.001, 0.01, n))

def test_ci_orders_low_below_high():
    r = _returns()
    lo, hi = stats.sharpe_ci(r, n_reps=200, seed=0)
    assert lo < hi

def test_ci_brackets_point_estimate_usually():
    r = _returns()
    point = np.sqrt(252) * r.mean() / r.std()
    lo, hi = stats.sharpe_ci(r, n_reps=500, seed=0)
    assert lo <= point <= hi

def test_ci_is_deterministic_with_seed():
    r = _returns()
    assert stats.sharpe_ci(r, n_reps=200, seed=42) == stats.sharpe_ci(r, n_reps=200, seed=42)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_stats.py -v`
Expected: FAIL with `ModuleNotFoundError` on `isa.stats`

- [ ] **Step 3: Write minimal implementation**

```python
# src/isa/stats.py
import numpy as np
import pandas as pd
from arch.bootstrap import StationaryBootstrap

def _auto_block(n):
    return max(1, int(round(n ** (1 / 3))))

def _sharpe(x):
    x = np.asarray(x).ravel()
    s = x.std()
    return float(np.sqrt(252) * x.mean() / s) if s else 0.0

def bootstrap_ci(returns, metric_fn, n_reps=1000, block_size=None, alpha=0.05, seed=0):
    arr = np.asarray(returns, dtype=float)
    block = block_size or _auto_block(len(arr))
    bs = StationaryBootstrap(block, arr, seed=seed)
    stats_out = []
    for data, _ in bs.bootstrap(n_reps):
        stats_out.append(metric_fn(data[0][0]))
    lo = float(np.percentile(stats_out, 100 * alpha / 2))
    hi = float(np.percentile(stats_out, 100 * (1 - alpha / 2)))
    return lo, hi

def sharpe_ci(returns, **kw):
    return bootstrap_ci(returns, _sharpe, **kw)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_stats.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/isa/stats.py tests/test_stats.py
git commit -m "feat: stationary bootstrap confidence intervals for metrics"
```

---

### Task 9: Results store (append-only Parquet + equity curves)

**Files:**
- Create: `src/isa/results.py`
- Test: `tests/test_results.py`

**Interfaces:**
- Consumes: `isa.engine.BacktestResult`
- Produces:
  - `RESULT_COLUMNS = ["strategy_id", "run_date", "universe", "metric", "value", "ci_low", "ci_high", "params_hash"]`
  - `params_hash(params: dict) -> str` (stable short hash)
  - `append_result(strategy_id, run_date, universe, metrics: dict, cis: dict, params: dict, root="results") -> None` (appends one row per metric to `results/runs.parquet`)
  - `save_equity_curve(strategy_id, universe, equity: pandas.Series, root="results") -> str`
  - `load_results(root="results") -> pandas.DataFrame`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_results.py
import pandas as pd
from isa import results

def test_params_hash_stable():
    assert results.params_hash({"a": 1, "b": 2}) == results.params_hash({"b": 2, "a": 1})

def test_append_and_load(tmp_path):
    root = str(tmp_path)
    results.append_result("ma_crossover", "2026-07-27", "index:sp500",
                          metrics={"sharpe": 1.2, "total_return": 0.4},
                          cis={"sharpe": (0.8, 1.6)}, params={"fast": 20}, root=root)
    df = results.load_results(root=root)
    assert set(df.columns) == set(results.RESULT_COLUMNS)
    sharpe_row = df[df["metric"] == "sharpe"].iloc[0]
    assert sharpe_row["value"] == 1.2
    assert sharpe_row["ci_low"] == 0.8 and sharpe_row["ci_high"] == 1.6
    tr_row = df[df["metric"] == "total_return"].iloc[0]
    assert pd.isna(tr_row["ci_low"])  # no CI provided

def test_append_is_cumulative(tmp_path):
    root = str(tmp_path)
    for d in ["2026-07-26", "2026-07-27"]:
        results.append_result("s", d, "AAPL", {"sharpe": 1.0}, {}, {}, root=root)
    assert len(results.load_results(root=root)) == 2

def test_save_equity_curve(tmp_path):
    root = str(tmp_path)
    s = pd.Series([1.0, 1.1], index=pd.to_datetime(["2024-01-02", "2024-01-03"]))
    p = results.save_equity_curve("s", "AAPL", s, root=root)
    assert p.endswith(".parquet")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_results.py -v`
Expected: FAIL with `ModuleNotFoundError` on `isa.results`

- [ ] **Step 3: Write minimal implementation**

```python
# src/isa/results.py
import hashlib, json, os
import pandas as pd

RESULT_COLUMNS = ["strategy_id", "run_date", "universe", "metric",
                  "value", "ci_low", "ci_high", "params_hash"]

def params_hash(params):
    blob = json.dumps(params, sort_keys=True, default=str).encode()
    return hashlib.sha1(blob).hexdigest()[:12]

def _runs_path(root):
    return os.path.join(root, "runs.parquet")

def append_result(strategy_id, run_date, universe, metrics, cis, params, root="results"):
    os.makedirs(root, exist_ok=True)
    ph = params_hash(params)
    rows = []
    for metric, value in metrics.items():
        lo, hi = cis.get(metric, (None, None))
        rows.append({"strategy_id": strategy_id, "run_date": run_date,
                     "universe": universe, "metric": metric, "value": value,
                     "ci_low": lo, "ci_high": hi, "params_hash": ph})
    new = pd.DataFrame(rows, columns=RESULT_COLUMNS)
    path = _runs_path(root)
    if os.path.exists(path):
        new = pd.concat([pd.read_parquet(path), new], ignore_index=True)
    new.to_parquet(path, index=False)

def save_equity_curve(strategy_id, universe, equity, root="results"):
    folder = os.path.join(root, "equity_curves")
    os.makedirs(folder, exist_ok=True)
    safe = universe.replace(":", "_")
    path = os.path.join(folder, f"{strategy_id}__{safe}.parquet")
    equity.rename("equity").to_frame().to_parquet(path)
    return path

def load_results(root="results"):
    path = _runs_path(root)
    if not os.path.exists(path):
        return pd.DataFrame(columns=RESULT_COLUMNS)
    return pd.read_parquet(path)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_results.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/isa/results.py tests/test_results.py
git commit -m "feat: append-only results store with equity curve persistence"
```

---

### Task 10: Runner orchestration (strategy x universe)

**Files:**
- Create: `src/isa/runner.py`
- Test: `tests/test_runner.py`

**Interfaces:**
- Consumes: `isa.strategy.discover_strategies`, `isa.universe.resolve_universe`, `isa.prices.read_universe_prices`, `isa.engine.run_backtest`, `isa.stats.sharpe_ci`, `isa.results.append_result`/`save_equity_curve`
- Produces:
  - `run_one(strategy_module, universe_spec, run_date, roots: dict) -> None` (resolve universe, load prices, backtest, compute sharpe CI, persist)
  - `run_all(universe_specs: list[str], run_date, strategies_folder="strategies", roots: dict|None=None) -> int` (returns number of (strategy, universe) results written)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_runner.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_runner.py -v`
Expected: FAIL with `ModuleNotFoundError` on `isa.runner`

- [ ] **Step 3: Write minimal implementation**

```python
# src/isa/runner.py
from isa import strategy, universe, prices, engine, stats, results

DEFAULT_ROOTS = {"price_root": "data/prices", "cat_root": "data/categories",
                 "theme_root": "data/themes", "results_root": "results"}

def run_one(strategy_module, universe_spec, run_date, roots):
    tickers = universe.resolve_universe(
        universe_spec, cat_root=roots["cat_root"],
        theme_root=roots["theme_root"], price_root=roots["price_root"])
    px = prices.read_universe_prices(tickers, root=roots["price_root"]).dropna(how="all")
    if px.empty:
        return False
    res = engine.run_backtest(strategy_module, px)
    cis = {}
    if len(res.returns) > 10:
        cis["sharpe"] = stats.sharpe_ci(res.returns, n_reps=500)
    results.append_result(strategy_module.META["id"], run_date, universe_spec,
                          res.metrics, cis, strategy_module.META.get("params", {}),
                          root=roots["results_root"])
    results.save_equity_curve(strategy_module.META["id"], universe_spec,
                              res.equity_curve, root=roots["results_root"])
    return True

def run_all(universe_specs, run_date, strategies_folder="strategies", roots=None):
    roots = roots or DEFAULT_ROOTS
    mods = strategy.discover_strategies(strategies_folder)
    count = 0
    for mod in mods:
        for spec in universe_specs:
            try:
                if run_one(mod, spec, run_date, roots):
                    count += 1
            except Exception as e:
                print(f"skip {mod.META['id']} x {spec}: {e}")
    return count
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_runner.py -v`
Expected: PASS (1 test)

- [ ] **Step 5: Commit**

```bash
git add src/isa/runner.py tests/test_runner.py
git commit -m "feat: runner orchestrating strategies across universes with CIs"
```

---

### Task 11: Static dashboard generation (DuckDB + Plotly)

**Files:**
- Create: `src/isa/build_site.py`
- Test: `tests/test_build_site.py`

**Interfaces:**
- Consumes: `isa.results.load_results`, equity-curve Parquet files under `results/equity_curves/`
- Produces:
  - `comparison_table(results_df) -> pandas.DataFrame` (pivot: one row per strategy+universe, columns per metric = value)
  - `build_site(results_root="results", out_dir="site") -> str` (writes `site/index.html` containing a metric comparison table and at least one Plotly chart; returns path). Charts obey: zero-baseline bars, dot/slope for change emphasis, no emojis.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_build_site.py
import os
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
    path = build_site.build_site(results_root=root, out_dir=out)
    assert os.path.exists(path)
    html = open(path, encoding="utf-8").read()
    assert "s1" in html
    # no emojis in output
    assert all(ord(ch) < 0x1F000 for ch in html)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_build_site.py -v`
Expected: FAIL with `ModuleNotFoundError` on `isa.build_site`

- [ ] **Step 3: Write minimal implementation**

```python
# src/isa/build_site.py
import os
import pandas as pd
import plotly.graph_objects as go
from plotly.io import to_html
from isa import results as results_mod

def comparison_table(results_df):
    if results_df.empty:
        return pd.DataFrame()
    df = results_df.copy()
    df["row"] = df["strategy_id"] + " | " + df["universe"]
    return df.pivot_table(index="row", columns="metric", values="value", aggfunc="last")

def _sharpe_dot_chart(results_df):
    sh = results_df[results_df["metric"] == "sharpe"].copy()
    if sh.empty:
        return ""
    sh["row"] = sh["strategy_id"] + " | " + sh["universe"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sh["value"], y=sh["row"], mode="markers", name="Sharpe",
        error_x=dict(type="data",
                     array=(sh["ci_high"] - sh["value"]).fillna(0),
                     arrayminus=(sh["value"] - sh["ci_low"]).fillna(0))))
    fig.update_layout(title="Sharpe by strategy (dot plot with 95% CI)",
                      xaxis_title="Sharpe", yaxis_title="")
    return to_html(fig, include_plotlyjs="cdn", full_html=False)

def build_site(results_root="results", out_dir="site"):
    os.makedirs(out_dir, exist_ok=True)
    df = results_mod.load_results(root=results_root)
    table_html = comparison_table(df).to_html(border=0, na_rep="")
    chart_html = _sharpe_dot_chart(df) if not df.empty else ""
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Investment Strategy Analysis</title></head>
<body>
<h1>Investment Strategy Analysis</h1>
<h2>Strategy comparison</h2>
{table_html}
<h2>Risk-adjusted performance</h2>
{chart_html}
</body></html>"""
    path = os.path.join(out_dir, "index.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_build_site.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add src/isa/build_site.py tests/test_build_site.py
git commit -m "feat: static plotly dashboard with sharpe dot plot and comparison table"
```

---

### Task 12: CLI entry point (update, seed, run, build)

**Files:**
- Create: `src/isa/cli.py`
- Modify: `pyproject.toml` (add `[project.scripts]` entry `isa = "isa.cli:main"`)
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `isa.runner.run_all`, `isa.build_site.build_site`, `isa.fetch.update_ticker`, `isa.seed_categories.main`, `isa.universe.resolve_universe`
- Produces: `main(argv: list[str] | None = None) -> int` with subcommands `seed`, `update`, `run`, `build`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cli.py
from isa import cli

def test_build_subcommand_runs(tmp_path):
    from isa import results
    rroot = str(tmp_path / "results")
    results.append_result("s1", "2026-07-27", "AAPL", {"sharpe": 1.0}, {}, {}, root=rroot)
    out = str(tmp_path / "site")
    rc = cli.main(["build", "--results-root", rroot, "--out-dir", out])
    assert rc == 0
    assert (tmp_path / "site" / "index.html").exists()

def test_unknown_command_returns_nonzero():
    assert cli.main(["nope"]) != 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli.py -v`
Expected: FAIL with `ModuleNotFoundError` on `isa.cli`

- [ ] **Step 3: Write minimal implementation**

```python
# src/isa/cli.py
import argparse
from isa import runner, build_site, fetch, universe

def main(argv=None):
    parser = argparse.ArgumentParser(prog="isa")
    sub = parser.add_subparsers(dest="cmd")

    p_seed = sub.add_parser("seed")
    p_update = sub.add_parser("update")
    p_update.add_argument("--universe", default="index:sp500")
    p_run = sub.add_parser("run")
    p_run.add_argument("--universes", nargs="+", default=["index:sp500"])
    p_run.add_argument("--run-date", default="today")
    p_build = sub.add_parser("build")
    p_build.add_argument("--results-root", default="results")
    p_build.add_argument("--out-dir", default="site")

    args = parser.parse_args(argv)
    if args.cmd == "seed":
        from isa import seed_categories
        seed_categories.main()
        return 0
    if args.cmd == "update":
        for t in universe.resolve_universe(args.universe):
            fetch.update_ticker(t)
        return 0
    if args.cmd == "run":
        run_date = args.run_date
        if run_date == "today":
            import datetime
            run_date = datetime.date.today().isoformat()
        runner.run_all(args.universes, run_date)
        return 0
    if args.cmd == "build":
        build_site.build_site(results_root=args.results_root, out_dir=args.out_dir)
        return 0
    print("unknown command")
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
```

Add to `pyproject.toml`:

```toml
[project.scripts]
isa = "isa.cli:main"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_cli.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add src/isa/cli.py pyproject.toml tests/test_cli.py
git commit -m "feat: isa CLI with seed/update/run/build subcommands"
```

---

### Task 13: GitHub Actions workflow + Pages deploy

**Files:**
- Create: `.github/workflows/scheduled-run.yml`
- Create: `docs/RUNBOOK.log`
- Test: manual validation (documented below); plus `tests/test_workflow_yaml.py`

**Interfaces:**
- Consumes: the `isa` CLI (`seed`, `update`, `run`, `build`)
- Produces: a scheduled + manually-dispatchable workflow that updates data, runs strategies, builds the site, commits results, and deploys `site/` to GitHub Pages

- [ ] **Step 1: Write the failing test**

```python
# tests/test_workflow_yaml.py
import yaml

def test_workflow_is_valid_and_has_schedule():
    with open(".github/workflows/scheduled-run.yml") as f:
        wf = yaml.safe_load(f)
    # 'on' may parse as True in YAML; check both
    trigger = wf.get("on", wf.get(True))
    assert "schedule" in trigger
    assert "workflow_dispatch" in trigger
    steps = wf["jobs"]["run"]["steps"]
    runs = " ".join(s.get("run", "") for s in steps)
    assert "isa update" in runs and "isa run" in runs and "isa build" in runs
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_workflow_yaml.py -v`
Expected: FAIL with `FileNotFoundError` on the workflow file

- [ ] **Step 3: Write the workflow and runbook**

```yaml
# .github/workflows/scheduled-run.yml
name: scheduled-run
on:
  schedule:
    - cron: "17 6 * * 1"  # weekly, Monday 06:17 UTC
  workflow_dispatch:
    inputs:
      universes:
        description: "space-separated universe specs"
        default: "index:sp500"
permissions:
  contents: write
  pages: write
  id-token: write
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          lfs: true
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Cache price store
        uses: actions/cache@v4
        with:
          path: data/prices
          key: prices-${{ github.run_id }}
          restore-keys: prices-
      - run: pip install -r requirements.txt && pip install -e .
      - run: isa seed
      - run: isa update --universe "index:sp500"
      - run: isa run --universes ${{ github.event.inputs.universes || 'index:sp500' }}
      - run: isa build --out-dir site
      - name: Commit results
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add results data/categories
          git commit -m "chore: scheduled run results" || echo "no changes"
          git push || echo "nothing to push"
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site
      - uses: actions/deploy-pages@v4
```

```
# docs/RUNBOOK.log
- Runbook
    - Local usage
        - Install: pip install -r requirements.txt && pip install -e .
        - Seed categories: isa seed
        - Update prices: isa update --universe index:sp500
        - Run backtests: isa run --universes index:sp500 sector:Technology
        - Build dashboard: isa build --out-dir site
        - Open site/index.html in a browser
    - GitHub Actions
        - Runs weekly on Monday plus manual dispatch
        - Requires Pages enabled with GitHub Actions as the source
        - Price files cached between runs, results committed back to the repo
    - Adding a ticker manually
        - Drop a Parquet file in data/prices named TICKER.parquet with the standard columns
        - It is picked up automatically by universe:all and any category it belongs to
    - Adding a strategy
        - Create strategies/<id>.py with a META dict and a generate function
        - It is discovered automatically on the next run and appears on the dashboard
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_workflow_yaml.py -v`
Expected: PASS (1 test)

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/scheduled-run.yml docs/RUNBOOK.log tests/test_workflow_yaml.py
git commit -m "feat: scheduled github actions workflow with pages deploy and runbook"
```

---

### Task 14: Full suite green + README and STATUS refresh

**Files:**
- Modify: `README.md`
- Modify: `STATUS.log`
- Test: whole suite

- [ ] **Step 1: Run the whole test suite**

Run: `python -m pytest -v`
Expected: all tests PASS

- [ ] **Step 2: Update README.md from the vision and current capabilities**

Replace the template with: project description from `readme.log`, the FOSS stack, quickstart commands from the runbook, and the status badge line `**Status**: 🔴 POC | **Mode**: 🤖 Claude Code | **Updated**: 2026-07-27`. No emojis beyond the existing badge legend. Use LaTeX for any math. No em dashes or semicolons.

- [ ] **Step 3: Update STATUS.log**

Set Last Updated to 2026-07-27, Stage to Proof of Concept, mark the POC success criteria that now hold (end-to-end flow demonstrated, stack validated), and list Tech Stack and Key Files.

- [ ] **Step 4: Run status sync script**

Run: `/home/k1/public/update_project_status.sh`
Expected: exits cleanly (skip if unavailable)

- [ ] **Step 5: Commit**

```bash
git add README.md STATUS.log
git commit -m "docs: refresh README and STATUS for POC completion"
```

---

## Self-Review

**Spec coverage:**
- Data ingestion (per-ticker Parquet, DuckDB, yfinance/Stooq, incremental update): Tasks 2, 3
- Categorization (SEC/yfinance/Wikipedia, sectors, membership, themes, universe resolution): Tasks 4, 5
- Backtesting all four kinds + metrics + confidence intervals + now-casting: Tasks 6, 7, 8
- Results storage (append-only Parquet, equity curves, CI bounds at write time): Task 9
- Runner across strategy x universe: Task 10
- Static dashboard on GitHub Pages (auto-listing, Plotly, zero-baseline/dot charts, no emojis): Task 11
- Scheduling on GitHub Actions + local parity via CLI: Tasks 12, 13
- Docs/status conventions: Tasks 13, 14
- git-LFS for price files: Task 1 (`.gitattributes`)

**Placeholder scan:** No TBD/TODO; every code step has concrete code; workflow and tests are complete.

**Type consistency:** `PRICE_COLUMNS` used consistently (Tasks 2, 3); `resolve_universe` signature identical across Tasks 4, 5, 10; `BacktestResult` fields (`equity_curve`, `returns`, `metrics`) consistent across Tasks 7, 10, 11; `RESULT_COLUMNS` consistent across Tasks 9, 10, 11; `roots` dict keys (`price_root`, `cat_root`, `theme_root`, `results_root`) consistent across Tasks 10, and the runner test seeds them identically.

**Notes for the implementer:**
- vectorbt import can be slow and pulls numba; the first test run may take time.
- Wikipedia and yfinance calls in `seed_categories.main`/`fetch._default_fetcher` are never exercised by tests (all tests inject data), so the suite runs offline.
