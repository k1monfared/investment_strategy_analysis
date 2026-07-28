- Investment Strategy Analysis: Design Spec
    - Status: approved design, pre-implementation
    - Date: 2026-07-27
    - Stage target: POC then MVP

- Goal
    - Build a process to define investment strategies, backtest them on historical data up to now, and do now-casting
    - Run any strategy across a single stock, a category, a theme, an index, or the whole market
    - Persist all results and publish an auto-growing dashboard that compares strategies with confidence intervals
    - Re-run everything on a schedule so data, results, and dashboard stay current
    - Host and run entirely on GitHub: scheduled runs via GitHub Actions, dashboard published to GitHub Pages

- Scope decisions
    - Market universe for v1: US stocks and ETFs only
    - Strategy types to support: signal/rule-based, portfolio allocation, screen and hold, buy-and-hold benchmark
    - Architecture: thin glue over mature FOSS libraries (Approach A), not a framework-agnostic core and not an all-in-one platform
    - Licensing: project is personal and open-source, never sold, so vectorbt OSS Commons Clause is acceptable
    - Data hosting: start on a small curated ticker set (S&P 500), one Parquet file per ticker, files grow independently, git-LFS for price files, manual ticker files allowed

- Chosen FOSS stack
    - Data ingestion: yfinance and Stooq for free price fetch, Parquet storage, DuckDB as query layer
    - Categorization: SEC EDGAR for SIC codes and ticker to CIK backbone, yfinance for sector and industry, Wikipedia index tables to seed membership, user tag files for themes
    - Backtesting: vectorbt OSS engine, quantstats and empyrical-reloaded for metrics, arch for bootstrap confidence intervals
    - Dashboard: static HTML site with embedded Plotly charts, published to GitHub Pages
    - Scheduling: GitHub Actions cron workflow, also runnable locally via the same entry script
    - Rationale detail lives in the research notes: [[research-notes]]

- Repository layout and data model
    - data/prices/
        - one Parquet file per ticker, git-LFS tracked, grows independently
        - columns: date, open, high, low, close, adj_close, volume
        - a hand-made file dropped here works as long as it matches the column schema
    - data/categories/
        - sectors.parquet: ticker to sector, industry, sic
        - membership.parquet: ticker to index with start and end dates
        - these are small and committed as plain files, not LFS
    - data/themes/
        - user-defined baskets as YAML, each is a list of tickers, e.g. clean_energy.yml
    - results/
        - runs.parquet: append-only rows of strategy_id, run_date, universe, metric, value, ci_low, ci_high, params_hash
        - equity_curves/: per strategy and universe curve for charts
    - strategies/
        - one Python file per strategy
    - site/
        - generated static dashboard, published to GitHub Pages
    - Key property: each ticker is an independent file, DuckDB reads them with a single glob so one file or ten thousand is the same query

- Strategy interface
    - A strategy is a single Python file in strategies/ exposing a META dict and a generate function
    - The author never touches vectorbt directly, the engine handles execution, costs, and metrics
    - META fields: id, name, kind, params
    - kind selects how the engine interprets the return value
        - signal: returns entries and exits boolean frames, per-ticker rules
        - portfolio: returns a weights frame, target weight per ticker per rebalance date
        - screen: returns a mask of which tickers to hold at each date, equal-weighted
        - benchmark: returns a fixed ticker list, buy and hold reference
    - generate receives price data and params and returns the kind-appropriate structure
    - Universe is named at run time and applied unchanged across the strategy
        - forms: a single ticker, a category such as sector:technology, a theme such as theme:clean_energy, an index such as index:sp500, or all
        - the runner loops the universe and writes one result row per strategy and universe
    - Discovery is automatic: dropping a file in strategies/ makes the runner and dashboard pick it up from META, no registration, no central list, this is what makes the dashboard grow over time

- Backtest engine and confidence intervals
    - A thin engine.py wraps vectorbt
    - Takes the strategy signals plus a universe price slice, applies fixed transaction costs and slippage, produces an equity curve plus metrics
    - Metrics via quantstats and empyrical-reloaded: total return, CAGR, Sharpe, Sortino, max drawdown, win rate
    - Confidence intervals via arch stationary bootstrap on the returns series, preserving autocorrelation, giving ci_low and ci_high on headline metrics
    - When a strategy runs across many tickers in a category, each ticker is a sample, yielding a cross-sectional distribution not just one number
    - Now-casting is a backtest whose end date is today

- Results storage and static dashboard
    - The runner appends one row per strategy, universe, run_date to results/runs.parquet and saves equity curves
    - A build_site.py step queries results with DuckDB and renders a static site
    - GitHub Pages cannot run Python, so the site is plain HTML with embedded Plotly charts via a static renderer, not a live server
    - The site auto-lists every strategy found in results, with comparison views: metric tables, equity-curve overlays, Sharpe and return comparisons as dot or slope charts
    - Visualization rules: bar charts start at zero, use line, dot, or slope charts to emphasize change, no emojis

- Scheduling on GitHub Actions
    - A single workflow, cron-triggered, daily or weekly or monthly configurable
    - Steps: checkout with LFS, update price files by fetching new bars per ticker, run all strategies over all universes, write results, build the static site, commit results, deploy site/ to GitHub Pages
    - Also runs on manual dispatch and locally via the same entry script, nothing is Actions-only

- Build order
    - Data layer: per-ticker Parquet fetch and update plus DuckDB reader on the S&P 500 set
    - Categorization: SEC plus yfinance plus Wikipedia seed into data/categories/
    - Engine plus one example strategy end-to-end on a few tickers
    - Results writer plus confidence intervals
    - Static dashboard generation
    - GitHub Actions workflow plus Pages deploy
    - Each step is independently testable and leaves the system working end-to-end on a growing scope

- Open items to revisit later
    - Scaling storage beyond the S&P 500 set to the whole market, and whether git-LFS quota holds
    - Whether to add a live local Streamlit view in addition to the static site
    - Transaction cost and slippage model defaults
