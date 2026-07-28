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
    p_build.add_argument("--strategies-folder", default="strategies")
    p_build.add_argument("--price-root", default="data/prices")
    p_build.add_argument("--cat-root", default="data/categories")
    p_build.add_argument("--no-export-prices", action="store_true",
                         help="skip exporting per-ticker price JSON for the explorer")

    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else 2
        return code if code else 2
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
        build_site.build_site(
            results_root=args.results_root, out_dir=args.out_dir,
            strategies_folder=args.strategies_folder,
            price_root=args.price_root, cat_root=args.cat_root,
            export_prices=not args.no_export_prices)
        return 0
    print("unknown command")
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
