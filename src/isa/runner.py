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
