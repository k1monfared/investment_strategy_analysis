"""Static multi-page dashboard generator.

Pages produced under out_dir:
  index.html                overview and strategy comparison
  strategies.html           index of all strategies, linking to detail pages
  strategy/<id>.html        full description of one strategy
  explorer.html             interactive price and portfolio and strategy explorer
  data/manifest.json        list of available tickers with sector
  data/strategies.json      strategy metadata for the explorer
  data/prices/<TICKER>.json compact price series for the explorer
  assets/style.css, assets/explorer.js

All charts obey the project rules: bar charts start at zero, change is shown with
line and dot charts, and there are no emojis in any output.
"""
import glob
import json
import os

import pandas as pd
import plotly.graph_objects as go
from plotly.io import to_html

from isa import results as results_mod
from isa import strategy as strategy_mod
from isa import web_assets

METRIC_ORDER = ["total_return", "cagr", "sharpe", "max_drawdown", "win_rate"]
METRIC_LABELS = {
    "total_return": "Total return",
    "cagr": "CAGR",
    "sharpe": "Sharpe",
    "max_drawdown": "Max drawdown",
    "win_rate": "Win rate",
}
PCT_METRICS = {"total_return", "cagr", "max_drawdown", "win_rate"}


# --------------------------------------------------------------------------- data

def comparison_table(results_df):
    if results_df.empty:
        return pd.DataFrame()
    df = results_df.copy()
    df["row"] = df["strategy_id"] + " | " + df["universe"]
    return df.pivot_table(index="row", columns="metric", values="value", aggfunc="last")


def _copy_plotly(assets_dir):
    """Copy the vendored Plotly bundle into the site assets directory."""
    src = os.path.join(os.path.dirname(__file__), "vendor", "plotly.min.js")
    dst = os.path.join(assets_dir, "plotly.min.js")
    if not os.path.exists(src):
        raise FileNotFoundError(
            f"vendored Plotly not found at {src}. Expected isa/vendor/plotly.min.js")
    import shutil
    shutil.copyfile(src, dst)
    return dst


def _load_strategies(folder):
    try:
        mods = strategy_mod.discover_strategies(folder)
    except Exception:
        mods = []
    out = []
    for m in mods:
        meta = m.META
        out.append({
            "id": meta["id"],
            "name": meta.get("name", meta["id"]),
            "kind": meta.get("kind", "signal"),
            "params": meta.get("params", {}),
            "description": meta.get("description", ""),
            "long_description": meta.get("long_description", ""),
            "references": meta.get("references", []),
            "client": meta.get("client"),
        })
    return out


# ----------------------------------------------------------------- shared HTML

def _page(title, active, body, depth=0):
    up = "../" * depth
    def nav(href, label, key):
        cls = " class=\"active\"" if key == active else ""
        return f"<a href=\"{up}{href}\"{cls}>{label}</a>"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="{up}assets/style.css">
<script src="{up}assets/plotly.min.js"></script>
</head>
<body>
<header class="topnav"><div class="wrap">
<span class="brand">Investment Strategy Analysis</span>
<nav>
{nav("index.html", "Overview", "overview")}
{nav("strategies.html", "Strategies", "strategies")}
{nav("explorer.html", "Explorer", "explorer")}
</nav>
</div></header>
<main>
{body}
</main>
<footer class="foot">
Generated static dashboard. Metrics come from committed backtest results. The Explorer
recomputes strategies in the browser for interactive comparison, so its numbers are
indicative and may differ slightly from the committed engine results.
</footer>
</body>
</html>"""


def _fmt_metric(metric, value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if metric in PCT_METRICS:
        return f"{value * 100:.1f}%"
    return f"{value:.2f}"


def _kind_badge(kind):
    return f'<span class="badge {kind}">{kind}</span>'


# ------------------------------------------------------------------- overview

def _overview_table_html(df):
    if df.empty:
        return "<p class='empty'>No results yet. Run isa run to populate the dashboard.</p>"
    piv = df.pivot_table(index=["strategy_id", "universe"], columns="metric",
                         values="value", aggfunc="last")
    metrics = [m for m in METRIC_ORDER if m in piv.columns]
    head = "".join(f"<th>{METRIC_LABELS[m]}</th>" for m in metrics)
    rows = []
    for (sid, uni), r in piv.iterrows():
        cells = []
        for m in metrics:
            v = r.get(m)
            txt = _fmt_metric(m, v)
            cls = ""
            if m in ("total_return", "cagr") and v is not None and not pd.isna(v):
                cls = " class=\"metric-pos\"" if v >= 0 else " class=\"metric-neg\""
            if m == "max_drawdown" and v is not None and not pd.isna(v):
                cls = " class=\"metric-neg\""
            cells.append(f"<td{cls}>{txt}</td>")
        link = f'<a href="strategy/{sid}.html">{sid}</a>'
        rows.append(f"<tr><td>{link}</td><td class='muted'>{uni}</td>{''.join(cells)}</tr>")
    return (f"<table class='data'><thead><tr><th>Strategy</th><th>Universe</th>{head}</tr>"
            f"</thead><tbody>{''.join(rows)}</tbody></table>")


def _sharpe_dot_chart(results_df):
    sh = results_df[results_df["metric"] == "sharpe"].copy()
    if sh.empty:
        return ""
    sh["row"] = sh["strategy_id"] + " | " + sh["universe"]
    sh = sh.sort_values("value")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sh["value"], y=sh["row"], mode="markers", name="Sharpe",
        marker=dict(size=9, color="#2b6cb0"),
        error_x=dict(type="data",
                     array=(sh["ci_high"] - sh["value"]).fillna(0),
                     arrayminus=(sh["value"] - sh["ci_low"]).fillna(0),
                     color="#a0aec0")))
    fig.update_layout(
        title="Sharpe by strategy and universe (dot plot with 95% CI)",
        xaxis_title="Sharpe", yaxis_title="", margin=dict(l=10, r=20, t=40, b=40),
        height=max(320, 26 * len(sh) + 120), template="simple_white")
    # Plotly is already loaded from the self-hosted assets/plotly.min.js in the page
    # head, so do not embed or link it again here.
    return to_html(fig, include_plotlyjs=False, full_html=False,
                   config={"displayModeBar": False})


def _overview_body(df):
    n_strats = df["strategy_id"].nunique() if not df.empty else 0
    n_unis = df["universe"].nunique() if not df.empty else 0
    return f"""
<h1>Overview</h1>
<p class="lead">Backtest results for every strategy across every universe that has been
run. Strategy names link to a full description of how each one works. Use the Explorer
to build a custom portfolio and compare strategies on it interactively.</p>
<div class="pill-row">
<span class="pill">{n_strats} strategies</span>
<span class="pill">{n_unis} universes</span>
<span class="pill">{len(df)} result rows</span>
</div>
<div class="card">
<h2>Risk-adjusted performance</h2>
{_sharpe_dot_chart(df) if not df.empty else "<p class='empty'>No results yet.</p>"}
<p class="hint">Higher Sharpe is better. Bars are 95% bootstrap confidence intervals on
the estimate.</p>
</div>
<div class="card">
<h2>Strategy comparison</h2>
{_overview_table_html(df)}
</div>
"""


# ------------------------------------------------------------- strategy pages

def _strategies_index_body(strategies):
    if not strategies:
        return "<h1>Strategies</h1><p class='empty'>No strategies found.</p>"
    cards = []
    for s in strategies:
        cards.append(f"""
<div class="card strat-card">
<h3><a href="strategy/{s['id']}.html">{s['name']}</a> {_kind_badge(s['kind'])}</h3>
<p class="desc">{s['description']}</p>
<p class="small muted">Parameters: <span class="params">{json.dumps(s['params'])}</span></p>
<a class="btn secondary" href="strategy/{s['id']}.html">Read the description</a>
</div>""")
    return f"""
<h1>Strategies</h1>
<p class="lead">Every strategy discovered in the project. Each one is a single Python
file that emits trading signals. Click through for a full explanation, parameters, and
how to read its results.</p>
<div class="grid">{''.join(cards)}</div>
"""


def _strategy_detail_body(s, df):
    sub = df[df["strategy_id"] == s["id"]] if not df.empty else pd.DataFrame()
    if not sub.empty:
        piv = sub.pivot_table(index="universe", columns="metric", values="value", aggfunc="last")
        metrics = [m for m in METRIC_ORDER if m in piv.columns]
        head = "".join(f"<th>{METRIC_LABELS[m]}</th>" for m in metrics)
        rows = []
        for uni, r in piv.iterrows():
            cells = "".join(f"<td>{_fmt_metric(m, r.get(m))}</td>" for m in metrics)
            rows.append(f"<tr><td>{uni}</td>{cells}</tr>")
        results_html = (f"<table class='data'><thead><tr><th>Universe</th>{head}</tr>"
                        f"</thead><tbody>{''.join(rows)}</tbody></table>")
    else:
        results_html = "<p class='empty'>No committed results for this strategy yet.</p>"

    long_html = "".join(f"<p>{para.strip()}</p>"
                        for para in s["long_description"].split("\n\n") if para.strip())
    refs = ""
    if s["references"]:
        items = "".join(f"<li>{r}</li>" for r in s["references"])
        refs = f"<h2>References</h2><ul>{items}</ul>"
    params_rows = "".join(
        f"<tr><td class='params'>{k}</td><td>{json.dumps(v)}</td></tr>"
        for k, v in s["params"].items()) or "<tr><td class='muted' colspan='2'>none</td></tr>"

    return f"""
<p class="small"><a href="../strategies.html">&larr; All strategies</a></p>
<h1>{s['name']} {_kind_badge(s['kind'])}</h1>
<p class="lead">{s['description']}</p>
<div class="card desc"><h2>How it works</h2>{long_html}</div>
<div class="card">
<h2>Parameters</h2>
<table class="data"><thead><tr><th>Name</th><th>Default</th></tr></thead>
<tbody>{params_rows}</tbody></table>
</div>
<div class="card">
<h2>Committed results</h2>
{results_html}
</div>
{('<div class="card">' + refs + '</div>') if refs else ''}
<p><a class="btn" href="../explorer.html">Compare it in the Explorer</a></p>
"""


# ----------------------------------------------------------------- explorer

def _explorer_body():
    return """
<h1>Explorer</h1>
<p class="lead">Build a portfolio by selecting tickers and assigning each a relative
weight, then chart its price over the full history. Layer on one or more strategies to
see how each would have performed on that exact portfolio, always compared against a
buy and hold baseline.</p>

<div class="card">
<div class="controls">
  <div class="control">
    <label for="smoothing">Frequency</label>
    <select id="smoothing">
      <option value="D">Daily</option>
      <option value="W">Weekly (last)</option>
      <option value="M">Monthly (last)</option>
      <option value="R">Rolling mean</option>
    </select>
  </div>
  <div class="control" id="rollwrap" style="display:none;">
    <label for="rollwin">Rolling window (days)</label>
    <input type="number" id="rollwin" value="20" min="2" step="1">
  </div>
  <div class="control">
    <label for="fee">Per-trade cost (fraction)</label>
    <input type="number" id="fee" value="0" min="0" step="0.0005">
  </div>
  <div class="control">
    <label>&nbsp;</label>
    <button class="btn" id="updateBtn">Update portfolio</button>
  </div>
  <div class="control">
    <label>&nbsp;</label>
    <button class="btn secondary" id="clearBtn">Clear</button>
  </div>
</div>
<p class="hint" id="status">Loading available tickers...</p>
</div>

<div class="explorer-grid">
  <div>
    <div class="card" style="padding:0;">
      <div class="searchbar"><input type="text" id="search" placeholder="Search tickers..."></div>
      <div class="picker" id="picker"></div>
    </div>
    <div class="card">
      <h3>Strategies</h3>
      <p class="hint">Select strategies to overlay on the portfolio.</p>
      <div class="strat-list" id="stratlist"></div>
    </div>
  </div>
  <div>
    <div class="card"><div class="chart" id="priceChart"></div></div>
    <div class="card">
      <div class="chart" id="stratChart"></div>
      <div id="stratMetrics"></div>
    </div>
  </div>
</div>
<script src="assets/explorer.js"></script>
"""


# --------------------------------------------------------------- data export

def _export_data(out_dir, price_root, cat_root, strategies):
    data_dir = os.path.join(out_dir, "data")
    prices_dir = os.path.join(data_dir, "prices")
    os.makedirs(prices_dir, exist_ok=True)

    # sector lookup
    sector_by_ticker = {}
    sectors_path = os.path.join(cat_root, "sectors.parquet")
    if os.path.exists(sectors_path):
        sec = pd.read_parquet(sectors_path)
        for _, r in sec.iterrows():
            sector_by_ticker[str(r["ticker"]).upper()] = r.get("sector") or "Uncategorized"

    tickers = []
    for p in sorted(glob.glob(os.path.join(price_root, "*.parquet"))):
        tk = os.path.splitext(os.path.basename(p))[0].upper()
        try:
            df = pd.read_parquet(p)[["date", "adj_close"]].dropna()
        except Exception:
            continue
        if df.empty:
            continue
        df = df.sort_values("date")
        d = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d").tolist()
        c = [round(float(x), 4) for x in df["adj_close"].tolist()]
        with open(os.path.join(prices_dir, f"{tk}.json"), "w", encoding="utf-8") as f:
            json.dump({"d": d, "c": c}, f, separators=(",", ":"))
        tickers.append({"t": tk, "s": sector_by_ticker.get(tk, "Uncategorized")})

    with open(os.path.join(data_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"tickers": tickers}, f, separators=(",", ":"))

    strat_public = [{
        "id": s["id"], "name": s["name"], "kind": s["kind"],
        "description": s["description"], "params": s["params"], "client": s["client"],
    } for s in strategies]
    with open(os.path.join(data_dir, "strategies.json"), "w", encoding="utf-8") as f:
        json.dump(strat_public, f, separators=(",", ":"))
    return len(tickers)


# ------------------------------------------------------------------- build

def build_site(results_root="results", out_dir="site",
               strategies_folder="strategies", price_root="data/prices",
               cat_root="data/categories", export_prices=True):
    os.makedirs(out_dir, exist_ok=True)
    assets_dir = os.path.join(out_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    with open(os.path.join(assets_dir, "style.css"), "w", encoding="utf-8") as f:
        f.write(web_assets.STYLE_CSS)
    with open(os.path.join(assets_dir, "explorer.js"), "w", encoding="utf-8") as f:
        f.write(web_assets.EXPLORER_JS)
    # self-hosted Plotly so charts render without any CDN dependency
    _copy_plotly(assets_dir)

    df = results_mod.load_results(root=results_root)
    strategies = _load_strategies(strategies_folder)

    # overview
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(_page("Investment Strategy Analysis", "overview", _overview_body(df)))

    # strategies index
    with open(os.path.join(out_dir, "strategies.html"), "w", encoding="utf-8") as f:
        f.write(_page("Strategies", "strategies", _strategies_index_body(strategies)))

    # per-strategy detail pages
    strat_dir = os.path.join(out_dir, "strategy")
    os.makedirs(strat_dir, exist_ok=True)
    for s in strategies:
        with open(os.path.join(strat_dir, f"{s['id']}.html"), "w", encoding="utf-8") as f:
            f.write(_page(s["name"], "strategies", _strategy_detail_body(s, df), depth=1))

    # explorer
    with open(os.path.join(out_dir, "explorer.html"), "w", encoding="utf-8") as f:
        f.write(_page("Explorer", "explorer", _explorer_body()))

    if export_prices:
        _export_data(out_dir, price_root, cat_root, strategies)

    return os.path.join(out_dir, "index.html")
