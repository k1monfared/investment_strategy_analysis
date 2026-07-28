# Investment Strategy Analysis

**Live dashboard: https://k1monfared.github.io/investment_strategy_analysis/**

**Status**: 🔴 POC | **Mode**: 🤖 Claude Code | **Updated**: 2026-07-28

A system to define investment strategies, backtest them on historical US stock and ETF
data up to the present, and do now-casting. Any strategy can be run across a single
stock, a sector, a theme, an index, or the whole market. All results are persisted and
an auto-growing static dashboard compares strategies with confidence intervals. The
whole pipeline re-runs on a schedule so data, results, and dashboard stay current, and
it is hosted entirely on GitHub: scheduled runs via GitHub Actions, dashboard published
to GitHub Pages.

## Table of contents

- [How it works](#how-it-works)
- [The dashboard](#the-dashboard)
- [FOSS stack](#foss-stack)
- [Repository layout](#repository-layout)
- [Local setup](#local-setup)
- [Running the pipeline locally](#running-the-pipeline-locally)
- [CLI reference](#cli-reference)
- [Universe specifications](#universe-specifications)
- [Adding a strategy](#adding-a-strategy)
- [Adding a ticker manually](#adding-a-ticker-manually)
- [Data model](#data-model)
- [Metrics and confidence intervals](#metrics-and-confidence-intervals)
- [Testing](#testing)
- [Continuous runs and deployment](#continuous-runs-and-deployment)
- [Conventions](#conventions)
- [Documentation](#documentation)

## How it works

- Price data lives as one Parquet file per ticker under `data/prices/`, git-LFS tracked
  and independently addable. DuckDB reads them with a single glob, so one file or ten
  thousand is the same query.
- A strategy is a single Python file in `strategies/` exposing a `META` dict and a
  `generate` function. Dropping in a new file makes the runner and dashboard pick it up
  automatically, which is what makes the dashboard grow over time.
- The engine wraps vectorbt, applies fixed costs and slippage, and produces an equity
  curve plus metrics. Confidence intervals come from a stationary bootstrap on the
  returns series, preserving autocorrelation. Now-casting is a backtest whose end date
  is today.
- Results append to `results/runs.parquet` with CI bounds stored at write time, and a
  build step renders a static Plotly dashboard to `site/`.

## The dashboard

`isa build` generates a static multi-page site under `site/`, published to GitHub Pages.
It is designed around three questions a user asks while exploring strategies.

### Overview (`index.html`)

The landing page answers "what is happening overall". It shows a Sharpe dot plot with
95 percent bootstrap confidence intervals and a full comparison table of every strategy
run against every universe. Strategy names link straight to their detail pages.

### Strategies (`strategies.html` and `strategy/<id>.html`)

Answers "what does each strategy actually do". The index lists every discovered strategy
as a card with its kind badge, one-line description, and parameters. Each links to a
detail page with:

- a full "How it works" explanation written in the strategy module,
- a parameter table with defaults,
- that strategy's committed results broken down by universe,
- references, when the author provides them.

Descriptions live in the strategy file itself. Add `description`, `long_description`,
and `references` to a strategy's `META` dict and they render automatically. See
[Adding a strategy](#adding-a-strategy).

### Explorer (`explorer.html`)

Answers "how would these behave on my portfolio". Fully interactive, computed in the
browser:

- Build a portfolio by ticking tickers (grouped by sector, with a search box) and typing
  a relative weight in the box next to each. Weights are normalized to a dollar-weighted
  index.
- Chart the portfolio value over its full history, indexed to 100 at the first common
  date. Choose the frequency: daily, weekly (last), monthly (last), or a rolling mean
  with a configurable window.
- Tick one or more strategies to overlay their equity curves on that exact portfolio,
  always drawn against a dotted buy and hold baseline, with a live metrics table
  (total return, CAGR, Sharpe, max drawdown). A per-trade cost input models friction.

To make this work `isa build` also exports, under `site/data/`, a compact price series
per ticker as JSON, a ticker and sector manifest, and strategy metadata. Each strategy
carries an optional `client` spec in its `META` so the browser can reproduce the rule.
Strategies without a `client` spec still appear but are disabled in the Explorer.

The Explorer recomputes strategies client-side for responsiveness, so its numbers are
indicative and can differ slightly from the committed Python engine results shown on the
Overview and detail pages.

## FOSS stack

- Data: yfinance, pandas, pyarrow, DuckDB
- Categorization: SEC EDGAR backbone, yfinance sectors, Wikipedia index tables, YAML themes
- Backtesting: vectorbt, quantstats, empyrical-reloaded, arch
- Dashboard: static HTML with embedded Plotly, published to GitHub Pages
- Scheduling: GitHub Actions cron, also runnable locally via the same CLI

## Repository layout

```
src/isa/            the isa package
  prices.py         per-ticker Parquet store and DuckDB universe reader
  fetch.py          incremental price fetch and update
  universe.py       resolve all, ticker, sector, index, theme specs
  seed_categories.py seed sectors and index membership from Wikipedia S&P 500
  strategy.py       META interface and auto-discovery of strategies
  engine.py         vectorbt backtest engine and core metrics
  stats.py          stationary bootstrap confidence intervals
  results.py        append-only results store and equity curves
  runner.py         orchestrates strategy x universe runs
  build_site.py     static Plotly dashboard generation
  cli.py            the isa command line entry point
strategies/         one Python file per strategy, discovered automatically
data/prices/        one Parquet file per ticker, git-LFS tracked
data/categories/    sectors.parquet and membership.parquet
data/themes/        user-defined baskets as YAML
results/            runs.parquet plus equity_curves/
site/               generated static dashboard
  index.html        overview: Sharpe dot plot and comparison table
  strategies.html   index of all strategies
  strategy/<id>.html per-strategy description, parameters, results
  explorer.html     interactive portfolio and strategy explorer
  assets/           style.css and explorer.js
  data/             manifest.json, strategies.json, prices/<TICKER>.json
tests/              pytest suite
docs/               specs, plans, and the runbook
.github/workflows/  scheduled-run.yml and deploy-pages.yml
```

## Local setup

Requires Python 3.11 or newer and git-lfs. Use a project-local virtual environment so
this project does not change the dependencies of anything else on your machine.

```bash
git clone https://github.com/k1monfared/investment_strategy_analysis.git
cd investment_strategy_analysis
git lfs install
git lfs pull                     # download the committed price files

python -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

The first import of vectorbt is slow because it pulls in numba, so the initial run or
test invocation takes longer than later ones.

## Running the pipeline locally

The whole pipeline is four commands, and the GitHub Actions workflow calls the same
ones, so nothing is CI only.

```bash
isa seed                                          # seed categories from Wikipedia S&P 500
isa update --universe index:sp500                 # fetch and update per-ticker price files
isa run --universes index:sp500 "sector:Information Technology"
isa build --out-dir site                          # generate the dashboard
```

Then open `site/index.html` in a browser. Because the Explorer fetches JSON with
`fetch`, browsers block it from a `file://` path, so serve the folder over HTTP to use
the Explorer locally:

```bash
python -m http.server -d site 8137
# then open http://127.0.0.1:8137/
```

The repository already ships with seeded categories, S&P 500 price history, backtest
results, and a built dashboard, so after `git lfs pull` you can go straight to
`isa run` or `isa build` without re-fetching anything.

## CLI reference

- `isa seed`
    - Seeds `data/categories/sectors.parquet` and `membership.parquet` from the
      Wikipedia S&P 500 table. Sends a descriptive User-Agent to avoid HTTP 403.
- `isa update --universe SPEC`
    - Fetches new daily bars for every ticker in the universe and appends only rows
      newer than the last stored date. Default `SPEC` is `index:sp500`.
- `isa run --universes SPEC [SPEC ...] [--run-date DATE]`
    - Runs every discovered strategy across each universe, computes metrics and a Sharpe
      confidence interval, and appends results. `--run-date` defaults to today.
- `isa build [--results-root results] [--out-dir site] [--strategies-folder strategies] [--price-root data/prices] [--cat-root data/categories] [--no-export-prices]`
    - Renders the full static dashboard: overview, strategies index, per-strategy detail
      pages, and the interactive Explorer. By default it also exports per-ticker price
      JSON, a ticker and sector manifest, and strategy metadata under `site/data/` so the
      Explorer works. Pass `--no-export-prices` to skip that export, for example when you
      only changed strategy descriptions and do not need to regenerate the price data.

## Universe specifications

A universe spec names what a strategy runs over, applied unchanged across the strategy.

- `all` every ticker present in `data/prices/`
- `AAPL` a single ticker
- `sector:Information Technology` all tickers in a GICS sector, names are exact
- `index:sp500` all current index constituents
- `theme:clean_energy` a user-defined YAML basket in `data/themes/clean_energy.yml`

Sector names are the exact GICS labels from the seed, for example
`Information Technology`, `Health Care`, `Financials`, `Energy`, not shorthand like
`Technology`.

## Adding a strategy

Create `strategies/<id>.py` with a `META` dict and a `generate` function. It is
discovered automatically on the next `isa run` and appears on the dashboard, with no
registration step.

```python
# strategies/ma_crossover.py
META = {
    "id": "ma_crossover",
    "name": "Moving Average Crossover",
    "kind": "signal",
    "params": {"fast": 20, "slow": 50},
    # Optional, powers the dashboard documentation pages:
    "description": "Hold when a fast moving average is above a slow one.",
    "long_description": "The moving average crossover is a trend-following rule...",
    "references": ["Brock, Lakonishok, and LeBaron (1992)"],
    # Optional, lets the Explorer reproduce the rule in the browser:
    "client": {"type": "sma_crossover", "fast": 20, "slow": 50},
}

def generate(prices, params):
    fast = prices.rolling(params["fast"]).mean()
    slow = prices.rolling(params["slow"]).mean()
    return {"entries": fast > slow, "exits": fast < slow}
```

Required `META` fields are `id`, `name`, `kind`, `params`. The `kind` selects how the
engine interprets the return value:

- `signal` returns `entries` and `exits` boolean frames, per-ticker rules
- `portfolio` returns a `weights` frame, target weight per ticker per rebalance
- `screen` returns a `mask` of which tickers to hold at each date, equal weighted
- `benchmark` returns a fixed ticker list, a buy and hold reference

Optional `META` fields enrich the dashboard:

- `description`: one-line summary shown on cards and listings
- `long_description`: multi-paragraph explanation rendered on the detail page. Separate
  paragraphs with a blank line.
- `references`: a list of citation strings shown on the detail page
- `client`: a small spec the browser Explorer uses to recompute the strategy live.
  Supported types are `buy_and_hold` and `sma_crossover` (with `fast` and `slow`). A
  strategy with no `client` spec still appears in the Explorer but is disabled there.

## Adding a ticker manually

Drop a Parquet file in `data/prices/` named `TICKER.parquet` with columns
`date, open, high, low, close, adj_close, volume`. It is picked up automatically by
`all` and by any category it belongs to. No code change is needed.

## Data model

- `data/prices/TICKER.parquet` columns: `date, open, high, low, close, adj_close, volume`
- `data/categories/sectors.parquet` columns: `ticker, sector, industry, sic`
- `data/categories/membership.parquet` columns: `ticker, index, start, end`
- `data/themes/NAME.yml`: a mapping with a `tickers` list
- `results/runs.parquet` columns: `strategy_id, run_date, universe, metric, value, ci_low, ci_high, params_hash`
- `results/equity_curves/STRATEGY__UNIVERSE.parquet`: one equity curve per run
- `site/data/manifest.json`: `{tickers: [{t: ticker, s: sector}]}` for the Explorer picker
- `site/data/strategies.json`: strategy metadata including the `client` spec
- `site/data/prices/TICKER.json`: `{d: [dates], c: [adj_close]}`, one compact series per
  ticker, consumed by the Explorer. Regenerated by `isa build` unless
  `--no-export-prices` is passed.

## Metrics and confidence intervals

Each backtest produces `total_return`, `cagr`, `sharpe`, `max_drawdown`, and `win_rate`.
Confidence intervals use a stationary block bootstrap on the returns series through the
`arch` library, which preserves autocorrelation. The Sharpe CI is stored as `ci_low` and
`ci_high` at write time so the dashboard stays read only and fast. When a strategy runs
across many tickers in a category, each ticker contributes to a cross-sectional
distribution rather than a single number.

## Testing

```bash
python -m pytest -q
```

All tests inject data or use fixtures, so the suite runs offline and does not hit
yfinance or Wikipedia.

## Continuous runs and deployment

Two workflows live in `.github/workflows/`:

- `scheduled-run.yml` runs weekly on Monday plus manual dispatch. It updates prices,
  runs all strategies over the chosen universes, builds the site, commits results back
  to the repo, and deploys `site/` to GitHub Pages.
- `deploy-pages.yml` runs on every push to `master` that touches `site/`, plus manual
  dispatch. It publishes the already-built `site/` directory to GitHub Pages, so the
  live dashboard updates as soon as you push a rebuilt site.

Pages is configured with GitHub Actions as the build source. Trigger a full data refresh
and deploy manually with:

```bash
gh workflow run scheduled-run.yml -f universes="index:sp500"
```

## Conventions

- Documentation is authored in loglog format as `*.log` files, converted to markdown
  when needed.
- Visualization rules: bar charts always start at zero, use line, dot, or slope charts
  to emphasize change, and no emojis in the web UI or generated HTML.
- Writing style in docs avoids em and en dashes and semicolons.

## Documentation

- `docs/RUNBOOK.log` - local and CI operations
- `docs/superpowers/specs/` - design spec and FOSS research notes
- `docs/superpowers/plans/` - task-by-task implementation plan
- `STATUS.log` - project status and progress tracking
- `CLAUDE.md` - Claude Code instructions and conventions

## Status Legend

- 🔴 POC / Early Stage
- 🟡 MVP / In Progress
- 🔵 Beta / Feature Complete
- 🟢 Production / Active
- ⚫ Maintenance / Template

## Mode Legend

- 🤖 Claude Code
- 👤 Manual
- 🔀 Hybrid
