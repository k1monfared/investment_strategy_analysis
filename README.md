# Investment Strategy Analysis

**Status**: 🔴 POC | **Mode**: 🤖 Claude Code | **Updated**: 2026-07-27

A system to define investment strategies, backtest them on historical US stock and ETF
data up to the present, and do now-casting. Any strategy can be run across a single
stock, a sector, a theme, an index, or the whole market. All results are persisted and
an auto-growing static dashboard compares strategies with confidence intervals. The
whole pipeline re-runs on a schedule so data, results, and dashboard stay current, and
it is hosted entirely on GitHub: scheduled runs via GitHub Actions, dashboard published
to GitHub Pages.

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

## FOSS stack

- Data: yfinance, pandas, pyarrow, DuckDB
- Categorization: SEC EDGAR backbone, yfinance sectors, Wikipedia index tables, YAML themes
- Backtesting: vectorbt, quantstats, empyrical-reloaded, arch
- Dashboard: static HTML with embedded Plotly, published to GitHub Pages
- Scheduling: GitHub Actions cron, also runnable locally via the same CLI

## Getting Started

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .

isa seed                                        # seed categories from Wikipedia S&P 500
isa update --universe index:sp500               # fetch and update price files
isa run --universes index:sp500 sector:Technology
isa build --out-dir site                        # generate the dashboard
```

Open `site/index.html` in a browser. See `docs/RUNBOOK.log` for full operational detail.

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
