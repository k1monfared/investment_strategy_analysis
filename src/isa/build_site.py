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
