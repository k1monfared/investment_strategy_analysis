"""Static assets (CSS and JavaScript) for the generated dashboard.

Kept as plain strings so build_site.py can write them verbatim. No emojis in any
generated output, per project visualization rules.
"""

# Plotly is self-hosted (vendored under isa/vendor/plotly.min.js and copied into
# site/assets/ by build_site) so the dashboard works offline and behind strict content
# security policies, instead of depending on a CDN that may be blocked.
PLOTLY_LOCAL = "assets/plotly.min.js"

STYLE_CSS = """
:root {
  --bg: #f7f8fa;
  --card: #ffffff;
  --ink: #1c2431;
  --muted: #5b6675;
  --line: #e2e6ec;
  --accent: #2b6cb0;
  --accent-weak: #ebf3fb;
  --good: #2f855a;
  --bad: #c53030;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: var(--ink);
  background: var(--bg);
  line-height: 1.55;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
header.topnav {
  background: var(--card);
  border-bottom: 1px solid var(--line);
  position: sticky;
  top: 0;
  z-index: 10;
}
.topnav .wrap {
  max-width: 1180px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  align-items: center;
  gap: 22px;
  height: 58px;
}
.topnav .brand { font-weight: 700; font-size: 16px; letter-spacing: 0.2px; }
.topnav nav { display: flex; gap: 18px; }
.topnav nav a { color: var(--muted); font-weight: 500; padding: 4px 2px; }
.topnav nav a.active { color: var(--ink); border-bottom: 2px solid var(--accent); }
main { max-width: 1180px; margin: 0 auto; padding: 28px 20px 64px; }
h1 { font-size: 26px; margin: 8px 0 4px; }
h2 { font-size: 20px; margin: 30px 0 12px; }
h3 { font-size: 16px; margin: 20px 0 8px; }
p.lead { color: var(--muted); font-size: 15px; max-width: 760px; }
.card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 18px 20px;
  margin: 14px 0;
}
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 14px; }
.badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--accent-weak);
  color: var(--accent);
}
.badge.benchmark { background: #f0e9fb; color: #6b46c1; }
.badge.signal { background: #e6f4ea; color: var(--good); }
.badge.portfolio { background: #fff2e0; color: #b7791f; }
.badge.screen { background: #e6f0fb; color: var(--accent); }
table.data { border-collapse: collapse; width: 100%; font-size: 14px; }
table.data th, table.data td { text-align: right; padding: 8px 10px; border-bottom: 1px solid var(--line); }
table.data th:first-child, table.data td:first-child { text-align: left; }
table.data thead th { color: var(--muted); font-weight: 600; border-bottom: 2px solid var(--line); }
table.data tbody tr:hover { background: #fafbfc; }
.metric-pos { color: var(--good); }
.metric-neg { color: var(--bad); }
.muted { color: var(--muted); }
.small { font-size: 13px; }
.params { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px; }
.desc p { max-width: 800px; }
.strat-card h3 { margin-top: 0; }
.strat-card .desc { color: var(--muted); font-size: 14px; }
.btn {
  display: inline-block;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 9px 16px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}
.btn:hover { background: #245c98; text-decoration: none; }
.btn.secondary { background: #fff; color: var(--accent); border: 1px solid var(--line); }
.btn.small { padding: 5px 10px; font-size: 12.5px; }
.controls { display: flex; flex-wrap: wrap; gap: 14px; align-items: flex-end; }
.control label { display: block; font-size: 12px; color: var(--muted); margin-bottom: 4px; font-weight: 600; }
.control input[type=text], .control input[type=number], .control input[type=date], .control select {
  padding: 7px 9px; border: 1px solid var(--line); border-radius: 7px; font-size: 14px; background: #fff;
}
.explorer-grid { display: grid; grid-template-columns: 340px 1fr; gap: 20px; align-items: start; }
@media (max-width: 900px) { .explorer-grid { grid-template-columns: 1fr; } }
.picker { max-height: 460px; overflow: auto; border: 1px solid var(--line); border-radius: 8px; }
.picker .sector { display: flex; align-items: center; gap: 8px; padding: 6px 10px; background: #f2f5f9; font-size: 12px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.4px; position: sticky; top: 0; cursor: pointer; }
.picker .sector:hover { background: #e9eef5; }
.picker .sector .sec-name { flex: 1; }
.picker .sector .sec-count { font-weight: 600; color: var(--accent); }
.picker .selectall { display: flex; align-items: center; gap: 8px; padding: 8px 10px; border-bottom: 1px solid var(--line); background: var(--accent-weak); font-size: 13px; font-weight: 700; color: var(--accent); position: sticky; top: 0; z-index: 2; cursor: pointer; }
.picker .row { display: flex; align-items: center; gap: 8px; padding: 5px 10px; border-bottom: 1px solid #f0f2f5; }
.picker .row:hover { background: #fafbfc; }
.picker .row .tk { flex: 1; font-size: 14px; }
.picker .row input[type=number] { width: 66px; padding: 4px 6px; border: 1px solid var(--line); border-radius: 6px; font-size: 13px; }
.picker .row input[type=number]:disabled { background: #f3f4f6; color: #b8bec7; }
.strat-list .row { display: flex; align-items: flex-start; gap: 9px; padding: 8px 4px; border-bottom: 1px solid var(--line); }
.strat-list .row .meta { flex: 1; }
.strat-list .row .meta .nm { font-weight: 600; font-size: 14px; }
.strat-list .row .meta .ds { font-size: 12.5px; color: var(--muted); }
.chart { width: 100%; min-height: 420px; }
.chart.short { min-height: 360px; }
.hint { font-size: 12.5px; color: var(--muted); margin: 6px 0 0; }
.searchbar { padding: 8px 10px; border-bottom: 1px solid var(--line); }
.searchbar input { width: 100%; padding: 7px 9px; border: 1px solid var(--line); border-radius: 7px; font-size: 14px; }
.pill-row { display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0; }
.pill { background: var(--accent-weak); color: var(--accent); border-radius: 999px; padding: 3px 10px; font-size: 12.5px; }
.empty { color: var(--muted); font-style: italic; padding: 18px 0; }
footer.foot { max-width: 1180px; margin: 0 auto; padding: 24px 20px 48px; color: var(--muted); font-size: 12.5px; border-top: 1px solid var(--line); }

/* info markers linking to the glossary */
.info {
  display: inline-flex; align-items: center; justify-content: center;
  width: 15px; height: 15px; margin-left: 5px;
  border-radius: 50%; background: var(--accent-weak); color: var(--accent);
  font-size: 10px; font-weight: 700; font-style: normal; line-height: 1;
  text-decoration: none; vertical-align: middle; cursor: help;
}
.info:hover { background: var(--accent); color: #fff; text-decoration: none; }
thead th .info { margin-left: 4px; }

/* glossary */
.glossary .term { border-bottom: 1px solid var(--line); padding: 20px 0; }
.glossary .term:last-child { border-bottom: none; }
.glossary h2 { margin-top: 0; scroll-margin-top: 74px; }
.glossary .term p { max-width: 820px; }
.glossary .term ul { max-width: 820px; }
.formula {
  background: #f2f5f9; border: 1px solid var(--line); border-radius: 6px;
  padding: 8px 12px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 13px; display: inline-block; margin: 6px 0; color: var(--ink);
}
.toc-inline { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0 4px; }
.toc-inline a { background: var(--accent-weak); border-radius: 999px; padding: 4px 11px; font-size: 13px; }
:target { background: #fff7e6; }

/* interactive overview controls */
.ov-strats { display: flex; flex-wrap: wrap; gap: 8px 18px; margin: 6px 0 2px; }
.ov-strat { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; }
#ovChart { width: 100%; min-height: 420px; }
""".strip()


# Shared client-side engine used by both the Explorer and the interactive Overview.
# Exposes a small window.ISA namespace so the page scripts stay thin.
ENGINE_JS = r"""
(function () {
  "use strict";
  var DATA = "data/";
  var priceCache = {};

  function fmtPct(x) {
    if (x === null || x === undefined || isNaN(x)) return "";
    return (x * 100).toFixed(1) + "%";
  }
  function fmtNum(x, d) {
    if (x === null || x === undefined || isNaN(x)) return "";
    return x.toFixed(d === undefined ? 2 : d);
  }

  function getJSON(url) {
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error("failed to load " + url);
      return r.json();
    });
  }

  function loadPrice(ticker) {
    if (priceCache[ticker]) return Promise.resolve(priceCache[ticker]);
    return getJSON(DATA + "prices/" + ticker + ".json").then(function (j) {
      priceCache[ticker] = j;
      return j;
    });
  }

  // Build a dollar-weighted portfolio index from selected tickers/weights.
  //
  // Dates are the UNION of every selected ticker's history, not the intersection, so a
  // ticker with a short history no longer truncates the whole portfolio. A ticker that
  // does not yet exist on a given date contributes 0 on that date. Each ticker is
  // normalized to 100 at its own first available date, and its fixed weight share is
  // applied whenever it is present. The result is that the index reflects only the
  // tickers that actually exist at each point in time, and newly listed tickers begin
  // contributing from their first traded day. Returns {dates:[...], values:[...]}.
  function buildPortfolio(selected) {
    var sets = selected.map(function (s) {
      var m = {};
      var d = s.data.d, c = s.data.c;
      for (var i = 0; i < d.length; i++) m[d[i]] = c[i];
      return m;
    });

    // union of all dates, chronological (YYYY-MM-DD sorts lexically)
    var dateSet = {};
    selected.forEach(function (s) {
      for (var i = 0; i < s.data.d.length; i++) dateSet[s.data.d[i]] = true;
    });
    var dates = Object.keys(dateSet).sort();
    if (dates.length === 0) return { dates: [], values: [] };

    var totalW = selected.reduce(function (a, s) { return a + s.weight; }, 0);
    if (totalW === 0) totalW = 1;

    // per-ticker normalization to 100 at its own first available date
    var norm = selected.map(function (s) {
      var first = s.data.c.length ? s.data.c[0] : 0;
      return first ? 100.0 / first : 0;
    });

    var values = [];
    for (var k = 0; k < dates.length; k++) {
      var dt = dates[k];
      var v = 0;
      for (var j = 0; j < sets.length; j++) {
        var price = sets[j][dt];
        if (price === undefined) continue;  // missing ticker contributes 0
        v += (selected[j].weight / totalW) * (price * norm[j]);
      }
      values.push(v);
    }
    return { dates: dates, values: values };
  }

  // ---- date windowing ----
  // dates are YYYY-MM-DD strings, so lexical comparison is chronological.
  function sliceByDate(series, start, end) {
    if (!start && !end) return series;
    var d = [], v = [];
    for (var i = 0; i < series.dates.length; i++) {
      var dt = series.dates[i];
      if (start && dt < start) continue;
      if (end && dt > end) continue;
      d.push(dt); v.push(series.values[i]);
    }
    return { dates: d, values: v };
  }
  function reindex(series) {
    if (series.values.length === 0) return series;
    var f = series.values[0];
    if (!f) return series;
    return { dates: series.dates, values: series.values.map(function (x) { return x / f * 100; }) };
  }

  // ---- smoothing ----
  function resampleLast(series, mode) {
    if (mode === "D") return series;
    var out = { dates: [], values: [] };
    var lastKey = null, lastIdx = -1;
    for (var i = 0; i < series.dates.length; i++) {
      var d = series.dates[i];
      var key;
      if (mode === "M") key = d.slice(0, 7);
      else key = weekKey(d);
      if (key !== lastKey && lastKey !== null) {
        out.dates.push(series.dates[lastIdx]);
        out.values.push(series.values[lastIdx]);
      }
      lastKey = key; lastIdx = i;
    }
    if (lastIdx >= 0) { out.dates.push(series.dates[lastIdx]); out.values.push(series.values[lastIdx]); }
    return out;
  }
  function weekKey(d) {
    var dt = new Date(d + "T00:00:00Z");
    var day = (dt.getUTCDay() + 6) % 7;
    dt.setUTCDate(dt.getUTCDate() - day);
    return dt.toISOString().slice(0, 10);
  }
  function rollingMean(series, win) {
    if (!win || win <= 1) return series;
    var out = { dates: series.dates.slice(), values: [] };
    var sum = 0, q = [];
    for (var i = 0; i < series.values.length; i++) {
      q.push(series.values[i]); sum += series.values[i];
      if (q.length > win) sum -= q.shift();
      out.values.push(sum / q.length);
    }
    return out;
  }

  // ---- client-side strategy engine ----
  function pctChange(values) {
    var r = [0];
    for (var i = 1; i < values.length; i++) r.push(values[i] / values[i - 1] - 1);
    return r;
  }
  function sma(values, win) {
    var out = [], sum = 0, q = [];
    for (var i = 0; i < values.length; i++) {
      q.push(values[i]); sum += values[i];
      if (q.length > win) sum -= q.shift();
      out.push(q.length < win ? NaN : sum / win);
    }
    return out;
  }
  function positionsFor(spec, values) {
    var n = values.length, pos = new Array(n).fill(0);
    if (!spec || spec.type === "buy_and_hold") { pos.fill(1); return pos; }
    if (spec.type === "sma_crossover") {
      var fast = sma(values, spec.fast), slow = sma(values, spec.slow);
      for (var i = 0; i < n; i++) {
        if (isNaN(fast[i]) || isNaN(slow[i])) pos[i] = 0;
        else pos[i] = fast[i] > slow[i] ? 1 : 0;
      }
      return pos;
    }
    pos.fill(1);
    return pos;
  }
  function equityFor(spec, portfolio, fee) {
    var vals = portfolio.values;
    var rets = pctChange(vals);
    var pos = positionsFor(spec, vals);
    var eq = [100.0];
    for (var i = 1; i < vals.length; i++) {
      var held = pos[i - 1];
      var r = held * rets[i];
      if (fee && i >= 2 && pos[i - 1] !== pos[i - 2]) r -= fee;
      eq.push(eq[i - 1] * (1 + r));
    }
    return { dates: portfolio.dates, values: eq };
  }
  function metrics(eq) {
    var v = eq.values;
    if (v.length < 2) return {};
    var total = v[v.length - 1] / v[0] - 1;
    var n = v.length;
    var years = n / 252;
    var cagr = years > 0 ? Math.pow(v[n - 1] / v[0], 1 / years) - 1 : 0;
    var rets = pctChange(v).slice(1);
    var mean = rets.reduce(function (a, b) { return a + b; }, 0) / rets.length;
    var variance = rets.reduce(function (a, b) { return a + (b - mean) * (b - mean); }, 0) / rets.length;
    var std = Math.sqrt(variance);
    var sharpe = std ? (mean / std) * Math.sqrt(252) : 0;
    var peak = v[0], mdd = 0;
    for (var i = 0; i < v.length; i++) { if (v[i] > peak) peak = v[i]; var dd = v[i] / peak - 1; if (dd < mdd) mdd = dd; }
    var winRate = rets.length ? rets.filter(function (x) { return x > 0; }).length / rets.length : 0;
    return { total: total, cagr: cagr, sharpe: sharpe, mdd: mdd, win: winRate };
  }

  window.ISA = {
    fmtPct: fmtPct, fmtNum: fmtNum, getJSON: getJSON, loadPrice: loadPrice,
    buildPortfolio: buildPortfolio, sliceByDate: sliceByDate, reindex: reindex,
    resampleLast: resampleLast, rollingMean: rollingMean,
    equityFor: equityFor, metrics: metrics
  };
})();
""".strip()


EXPLORER_JS = r"""
(function () {
  "use strict";

  var ISA = window.ISA;
  var manifest = null;
  var strategies = [];
  var fullPortfolio = null;  // full-history portfolio before date windowing

  var fmtPct = ISA.fmtPct, fmtNum = ISA.fmtNum;
  var getJSON = ISA.getJSON, loadPrice = ISA.loadPrice;
  var buildPortfolio = ISA.buildPortfolio, sliceByDate = ISA.sliceByDate, reindex = ISA.reindex;
  var equityFor = ISA.equityFor, metrics = ISA.metrics;

  function applySmoothing(series) {
    var mode = el("smoothing").value, win = parseInt(el("rollwin").value, 10);
    return mode === "R" ? ISA.rollingMean(series, win) : ISA.resampleLast(series, mode);
  }

  // ---- DOM helpers ----
  function el(id) { return document.getElementById(id); }
  function selectedTickers() {
    var out = [];
    document.querySelectorAll("#picker .row").forEach(function (row) {
      var cb = row.querySelector("input[type=checkbox]");
      if (cb.checked) {
        var w = parseFloat(row.querySelector("input[type=number]").value);
        if (isNaN(w) || w <= 0) w = 1;
        out.push({ ticker: cb.value, weight: w });
      }
    });
    return out;
  }
  function selectedStrategies() {
    var out = [];
    document.querySelectorAll("#stratlist .row").forEach(function (row) {
      var cb = row.querySelector("input[type=checkbox]");
      if (cb.checked) out.push(cb.value);
    });
    return out;
  }

  function renderPortfolioChart(portfolioRaw) {
    var series = applySmoothing(portfolioRaw);
    var trace = {
      x: series.dates, y: series.values, type: "scatter", mode: "lines",
      name: "Portfolio", line: { color: "#2b6cb0", width: 2 }
    };
    var layout = {
      margin: { l: 55, r: 20, t: 30, b: 40 },
      title: "Portfolio value (indexed to 100 at window start)",
      xaxis: { title: "" }, yaxis: { title: "Index" },
      hovermode: "x unified", showlegend: true
    };
    Plotly.newPlot("priceChart", [trace], layout, { responsive: true, displayModeBar: false });
  }

  function renderStrategyChart(portfolioRaw, stratIds) {
    var fee = parseFloat(el("fee").value);
    if (isNaN(fee)) fee = 0;
    var traces = [];
    var baseline = equityFor({ type: "buy_and_hold" }, portfolioRaw, 0);
    traces.push({ x: baseline.dates, y: baseline.values, type: "scatter", mode: "lines",
      name: "Buy and hold (baseline)", line: { color: "#a0aec0", width: 2, dash: "dot" } });

    var rows = [rowMetrics("Buy and hold (baseline)", metrics(baseline))];
    var palette = ["#2b6cb0", "#2f855a", "#b7791f", "#6b46c1", "#c53030", "#0987a0", "#b83280"];
    stratIds.forEach(function (id, idx) {
      var strat = strategies.filter(function (s) { return s.id === id; })[0];
      if (!strat || !strat.client) return;
      var eq = equityFor(strat.client, portfolioRaw, fee);
      traces.push({ x: eq.dates, y: eq.values, type: "scatter", mode: "lines",
        name: strat.name, line: { color: palette[idx % palette.length], width: 2 } });
      rows.push(rowMetrics(strat.name, metrics(eq)));
    });

    var layout = {
      margin: { l: 55, r: 20, t: 30, b: 40 },
      title: "Strategy equity curves on this portfolio (indexed to 100)",
      xaxis: { title: "" }, yaxis: { title: "Equity" },
      hovermode: "x unified", showlegend: true
    };
    Plotly.newPlot("stratChart", traces, layout, { responsive: true, displayModeBar: false });

    function hdr(label, key) {
      return "<th>" + label +
        "<a class='info' href='glossary.html#" + key + "' title='Open glossary'>i</a></th>";
    }
    el("stratMetrics").innerHTML =
      "<table class='data'><thead><tr><th>Strategy</th>" +
      hdr("Total return", "total_return") + hdr("CAGR", "cagr") +
      hdr("Sharpe", "sharpe") + hdr("Max drawdown", "max_drawdown") +
      hdr("Win rate", "win_rate") +
      "</tr></thead><tbody>" + rows.join("") + "</tbody></table>";
  }
  function rowMetrics(name, m) {
    function cls(x) { return x >= 0 ? "metric-pos" : "metric-neg"; }
    return "<tr><td>" + name + "</td>" +
      "<td class='" + cls(m.total) + "'>" + fmtPct(m.total) + "</td>" +
      "<td class='" + cls(m.cagr) + "'>" + fmtPct(m.cagr) + "</td>" +
      "<td>" + fmtNum(m.sharpe) + "</td>" +
      "<td class='metric-neg'>" + fmtPct(m.mdd) + "</td>" +
      "<td>" + fmtPct(m.win) + "</td></tr>";
  }

  function setDateBounds(portfolio) {
    var d = portfolio.dates;
    if (d.length === 0) return;
    var lo = d[0], hi = d[d.length - 1];
    var s = el("startDate"), e = el("endDate");
    s.min = lo; s.max = hi; e.min = lo; e.max = hi;
    s.value = lo; e.value = hi;
  }

  // Render for the currently selected date window using the cached full portfolio.
  function renderWindow() {
    if (!fullPortfolio || fullPortfolio.dates.length === 0) return;
    var start = el("startDate").value, end = el("endDate").value;
    if (start && end && start > end) { var t = start; start = end; end = t; }
    var win = sliceByDate(fullPortfolio, start, end);
    var status = el("status");
    if (win.dates.length < 2) {
      status.textContent = "The selected date window has too few trading days. Widen it.";
      el("priceChart").innerHTML = ""; el("stratChart").innerHTML = ""; el("stratMetrics").innerHTML = "";
      return;
    }
    var portfolio = reindex(win);
    status.textContent = win.dates.length + " trading days in window (" +
      win.dates[0] + " to " + win.dates[win.dates.length - 1] + ").";
    renderPortfolioChart(portfolio);
    var strats = selectedStrategies();
    if (strats.length > 0) renderStrategyChart(portfolio, strats);
    else {
      el("stratChart").innerHTML =
        "<p class='empty'>Select one or more strategies to compare them on this portfolio.</p>";
      el("stratMetrics").innerHTML = "";
    }
  }

  // Reload prices for the current ticker selection, rebuild the full portfolio,
  // reset the date window to the full range, then render.
  function rebuild() {
    var sel = selectedTickers();
    var status = el("status");
    if (sel.length === 0) {
      fullPortfolio = null;
      status.textContent = "Select at least one ticker to build a portfolio.";
      el("priceChart").innerHTML = ""; el("stratChart").innerHTML = ""; el("stratMetrics").innerHTML = "";
      return;
    }
    status.textContent = "Loading " + sel.length + " price series...";
    Promise.all(sel.map(function (s) {
      return loadPrice(s.ticker).then(function (data) {
        return { ticker: s.ticker, weight: s.weight, data: data };
      });
    })).then(function (loaded) {
      var portfolio = buildPortfolio(loaded);
      if (portfolio.dates.length === 0) {
        fullPortfolio = null;
        status.textContent = "Selected tickers have no overlapping dates.";
        return;
      }
      fullPortfolio = portfolio;
      setDateBounds(portfolio);
      renderWindow();
    }).catch(function (e) {
      status.textContent = "Error: " + e.message;
    });
  }

  // Set a ticker row's checkbox state and keep its weight box enabled/disabled in sync.
  function setRowChecked(row, checked) {
    var cb = row.querySelector("input[type=checkbox]");
    var wt = row.querySelector("input[type=number]");
    cb.checked = checked;
    wt.disabled = !checked;
  }

  // Reflect how many of a group's visible rows are checked on the parent checkbox,
  // using the indeterminate state when the selection is partial.
  function syncGroup(group) {
    var rows = group.querySelectorAll(".row");
    var boxes = group.querySelectorAll(".row input[type=checkbox]");
    var total = boxes.length, checked = 0;
    boxes.forEach(function (b) { if (b.checked) checked++; });
    var head = group.querySelector(".sector input[type=checkbox]");
    if (head) {
      head.checked = total > 0 && checked === total;
      head.indeterminate = checked > 0 && checked < total;
    }
    var cnt = group.querySelector(".sec-count");
    if (cnt) cnt.textContent = checked + "/" + total;
  }

  function syncAll() {
    var groups = document.querySelectorAll("#picker .sectorgroup");
    groups.forEach(syncGroup);
    var boxes = document.querySelectorAll("#picker .row input[type=checkbox]");
    var total = boxes.length, checked = 0;
    boxes.forEach(function (b) { if (b.checked) checked++; });
    var master = el("selectAll");
    if (master) {
      master.checked = total > 0 && checked === total;
      master.indeterminate = checked > 0 && checked < total;
    }
    var mc = el("selectAllCount");
    if (mc) mc.textContent = checked + "/" + total;
  }

  function buildPicker() {
    var bySector = {};
    manifest.tickers.forEach(function (t) {
      var s = t.s || "Uncategorized";
      (bySector[s] = bySector[s] || []).push(t.t);
    });
    var sectors = Object.keys(bySector).sort();
    var html = "";
    html += "<label class='selectall'>" +
      "<input type='checkbox' id='selectAll'>" +
      "<span class='sec-name'>All tickers</span>" +
      "<span class='sec-count' id='selectAllCount'></span></label>";
    sectors.forEach(function (sec) {
      html += "<div class='sectorgroup' data-sector='" + sec.toLowerCase() + "'>";
      html += "<label class='sector'>" +
        "<input type='checkbox' class='sec-toggle'>" +
        "<span class='sec-name'>" + sec + "</span>" +
        "<span class='sec-count'></span></label>";
      bySector[sec].sort().forEach(function (tk) {
        html += "<div class='row' data-ticker='" + tk.toLowerCase() + "'>" +
          "<input type='checkbox' value='" + tk + "'>" +
          "<span class='tk'>" + tk + "</span>" +
          "<input type='number' min='0' step='0.1' value='1' disabled title='Relative weight'>" +
          "</div>";
      });
      html += "</div>";
    });
    el("picker").innerHTML = html;

    // individual ticker rows
    document.querySelectorAll("#picker .row").forEach(function (row) {
      var cb = row.querySelector("input[type=checkbox]");
      cb.addEventListener("change", function () {
        row.querySelector("input[type=number]").disabled = !cb.checked;
        syncAll();
      });
    });

    // per-sector toggle: only affects rows currently visible under the search filter
    document.querySelectorAll("#picker .sectorgroup").forEach(function (group) {
      var head = group.querySelector(".sec-toggle");
      head.addEventListener("change", function () {
        var want = head.checked;
        group.querySelectorAll(".row").forEach(function (row) {
          if (row.style.display === "none") return;
          setRowChecked(row, want);
        });
        syncAll();
      });
    });

    // master toggle: affects all visible rows
    el("selectAll").addEventListener("change", function () {
      var want = el("selectAll").checked;
      document.querySelectorAll("#picker .row").forEach(function (row) {
        if (row.style.display === "none") return;
        setRowChecked(row, want);
      });
      syncAll();
    });

    syncAll();
  }

  function buildStrategyList() {
    var html = "";
    strategies.forEach(function (s) {
      var runnable = !!s.client;
      html += "<div class='row'>" +
        "<input type='checkbox' value='" + s.id + "'" + (runnable ? "" : " disabled") + ">" +
        "<div class='meta'><div class='nm'>" + s.name +
        (runnable ? "" : " <span class='muted small'>(not runnable in explorer)</span>") +
        "</div><div class='ds'>" + (s.description || "") + "</div></div></div>";
    });
    el("stratlist").innerHTML = html;
  }

  function wireControls() {
    el("updateBtn").addEventListener("click", rebuild);
    el("clearBtn").addEventListener("click", function () {
      document.querySelectorAll("#picker .row").forEach(function (row) {
        setRowChecked(row, false);
      });
      document.querySelectorAll("#stratlist input[type=checkbox]").forEach(function (cb) { cb.checked = false; });
      syncAll();
      rebuild();
    });
    el("smoothing").addEventListener("change", function () {
      el("rollwrap").style.display = this.value === "R" ? "block" : "none";
      renderWindow();
    });
    el("rollwin").addEventListener("change", renderWindow);
    el("fee").addEventListener("change", renderWindow);
    el("startDate").addEventListener("change", renderWindow);
    el("endDate").addEventListener("change", renderWindow);
    el("fullRangeBtn").addEventListener("click", function () {
      if (fullPortfolio) { setDateBounds(fullPortfolio); renderWindow(); }
    });
    // recompute strategy overlays live when the strategy selection changes
    document.addEventListener("change", function (ev) {
      if (ev.target && ev.target.closest && ev.target.closest("#stratlist")) renderWindow();
    });
    el("search").addEventListener("input", function () {
      var q = this.value.trim().toLowerCase();
      document.querySelectorAll("#picker .sectorgroup").forEach(function (g) {
        var any = false;
        g.querySelectorAll(".row").forEach(function (r) {
          var show = !q || r.getAttribute("data-ticker").indexOf(q) > -1;
          r.style.display = show ? "flex" : "none";
          if (show) any = true;
        });
        g.style.display = any ? "block" : "none";
      });
    });
  }

  function init() {
    Promise.all([getJSON(DATA + "manifest.json"), getJSON(DATA + "strategies.json")])
      .then(function (res) {
        manifest = res[0]; strategies = res[1];
        buildPicker(); buildStrategyList(); wireControls();
        el("status").textContent =
          manifest.tickers.length + " tickers available. Select some and press Update portfolio.";
      })
      .catch(function (e) {
        el("status").textContent = "Could not load data files: " + e.message;
      });
  }

  if (document.readyState !== "loading") init();
  else document.addEventListener("DOMContentLoaded", init);
})();
""".strip()


# Interactive comparison on the Overview page: pick a universe (all or a sector), a date
# window, and strategies, then recompute an equal-weight backtest in the browser.
OVERVIEW_JS = r"""
(function () {
  "use strict";
  var ISA = window.ISA;
  var manifest = null;
  var strategies = [];
  var fullPortfolio = null;
  var universeSize = 0;

  function el(id) { return document.getElementById(id); }
  var fmtPct = ISA.fmtPct, fmtNum = ISA.fmtNum;

  function universeTickers() {
    var u = el("ovUniverse").value;
    return manifest.tickers.filter(function (t) {
      return u === "all" ? true : (t.s === u);
    }).map(function (t) { return t.t; });
  }

  function selectedStrategies() {
    var out = [];
    document.querySelectorAll("#ovStrats input[type=checkbox]:checked").forEach(function (cb) {
      out.push(cb.value);
    });
    return out;
  }

  function setDateBounds(portfolio) {
    var d = portfolio.dates;
    if (!d.length) return;
    var s = el("ovStart"), e = el("ovEnd");
    s.min = d[0]; s.max = d[d.length - 1];
    e.min = d[0]; e.max = d[d.length - 1];
    s.value = d[0]; e.value = d[d.length - 1];
  }

  function render() {
    if (!fullPortfolio || !fullPortfolio.dates.length) return;
    var start = el("ovStart").value, end = el("ovEnd").value;
    if (start && end && start > end) { var t = start; start = end; end = t; }
    var win = ISA.sliceByDate(fullPortfolio, start, end);
    if (win.dates.length < 2) {
      el("ovStatus").textContent = "The selected date window has too few trading days. Widen it.";
      el("ovChart").innerHTML = ""; el("ovMetrics").innerHTML = "";
      return;
    }
    var portfolio = ISA.reindex(win);
    el("ovStatus").textContent = universeSize + " tickers, equal weighted. Window " +
      win.dates[0] + " to " + win.dates[win.dates.length - 1] + " (" + win.dates.length + " days).";

    var fee = parseFloat(el("ovFee").value);
    if (isNaN(fee)) fee = 0;
    var traces = [];
    var baseline = ISA.equityFor({ type: "buy_and_hold" }, portfolio, 0);
    traces.push({ x: baseline.dates, y: baseline.values, type: "scatter", mode: "lines",
      name: "Buy and hold (baseline)", line: { color: "#a0aec0", width: 2, dash: "dot" } });
    var rows = [rowMetrics("Buy and hold (baseline)", ISA.metrics(baseline))];

    var palette = ["#2b6cb0", "#2f855a", "#b7791f", "#6b46c1", "#c53030", "#0987a0", "#b83280"];
    selectedStrategies().forEach(function (id, idx) {
      var strat = strategies.filter(function (s) { return s.id === id; })[0];
      if (!strat || !strat.client) return;
      var eq = ISA.equityFor(strat.client, portfolio, fee);
      traces.push({ x: eq.dates, y: eq.values, type: "scatter", mode: "lines",
        name: strat.name, line: { color: palette[idx % palette.length], width: 2 } });
      rows.push(rowMetrics(strat.name, ISA.metrics(eq)));
    });

    var layout = {
      margin: { l: 55, r: 20, t: 40, b: 40 },
      title: "Equity curves on the selected universe and window (indexed to 100)",
      xaxis: { title: "" }, yaxis: { title: "Equity" },
      hovermode: "x unified", showlegend: true
    };
    Plotly.newPlot("ovChart", traces, layout, { responsive: true, displayModeBar: false });

    function hdr(label, key) {
      return "<th>" + label + "<a class='info' href='glossary.html#" + key +
        "' title='Open glossary'>i</a></th>";
    }
    el("ovMetrics").innerHTML =
      "<table class='data'><thead><tr><th>Strategy</th>" +
      hdr("Total return", "total_return") + hdr("CAGR", "cagr") +
      hdr("Sharpe", "sharpe") + hdr("Max drawdown", "max_drawdown") +
      hdr("Win rate", "win_rate") + "</tr></thead><tbody>" + rows.join("") + "</tbody></table>";
  }

  function rowMetrics(name, m) {
    function cls(x) { return x >= 0 ? "metric-pos" : "metric-neg"; }
    return "<tr><td>" + name + "</td>" +
      "<td class='" + cls(m.total) + "'>" + fmtPct(m.total) + "</td>" +
      "<td class='" + cls(m.cagr) + "'>" + fmtPct(m.cagr) + "</td>" +
      "<td>" + fmtNum(m.sharpe) + "</td>" +
      "<td class='metric-neg'>" + fmtPct(m.mdd) + "</td>" +
      "<td>" + fmtPct(m.win) + "</td></tr>";
  }

  function rebuild() {
    var tickers = universeTickers();
    universeSize = tickers.length;
    if (tickers.length === 0) {
      el("ovStatus").textContent = "No tickers in this universe.";
      return;
    }
    el("ovStatus").textContent = "Loading " + tickers.length + " price series, please wait...";
    Promise.all(tickers.map(function (tk) {
      return ISA.loadPrice(tk).then(function (data) {
        return { ticker: tk, weight: 1, data: data };
      }).catch(function () { return null; });
    })).then(function (loaded) {
      loaded = loaded.filter(function (x) { return x && x.data && x.data.d.length; });
      universeSize = loaded.length;
      var portfolio = ISA.buildPortfolio(loaded);
      if (!portfolio.dates.length) {
        el("ovStatus").textContent = "No price data for this universe.";
        return;
      }
      fullPortfolio = portfolio;
      setDateBounds(portfolio);
      render();
    }).catch(function (e) {
      el("ovStatus").textContent = "Error: " + e.message;
    });
  }

  function buildUniverseOptions() {
    var secs = {};
    manifest.tickers.forEach(function (t) { secs[t.s || "Uncategorized"] = true; });
    var opts = "<option value='all'>All tickers (" + manifest.tickers.length + ")</option>";
    Object.keys(secs).sort().forEach(function (s) {
      var n = manifest.tickers.filter(function (t) { return t.s === s; }).length;
      opts += "<option value='" + s + "'>" + s + " (" + n + ")</option>";
    });
    el("ovUniverse").innerHTML = opts;
  }

  function buildStrategyChecks() {
    var html = "";
    strategies.forEach(function (s) {
      var runnable = !!s.client;
      html += "<label class='ov-strat'>" +
        "<input type='checkbox' value='" + s.id + "'" +
        (runnable ? " checked" : " disabled") + "> " + s.name +
        (runnable ? "" : " <span class='muted small'>(not runnable here)</span>") + "</label>";
    });
    el("ovStrats").innerHTML = html;
  }

  function wire() {
    el("ovRun").addEventListener("click", rebuild);
    el("ovStart").addEventListener("change", render);
    el("ovEnd").addEventListener("change", render);
    el("ovFee").addEventListener("change", render);
    el("ovFullRange").addEventListener("click", function () {
      if (fullPortfolio) { setDateBounds(fullPortfolio); render(); }
    });
    el("ovStrats").addEventListener("change", render);
    // reloading a whole universe is expensive, so only the Run button triggers it
    el("ovUniverse").addEventListener("change", function () {
      el("ovStatus").textContent = "Universe changed. Press Run to load it.";
    });
  }

  function init() {
    Promise.all([ISA.getJSON("data/manifest.json"), ISA.getJSON("data/strategies.json")])
      .then(function (res) {
        manifest = res[0]; strategies = res[1];
        buildUniverseOptions(); buildStrategyChecks(); wire();
        // default to a single sector so the first load is fast
        var firstSector = null;
        var secs = {};
        manifest.tickers.forEach(function (t) { secs[t.s] = true; });
        firstSector = Object.keys(secs).sort()[0];
        if (firstSector) el("ovUniverse").value = firstSector;
        rebuild();
      })
      .catch(function (e) {
        el("ovStatus").textContent = "Could not load data files: " + e.message;
      });
  }

  if (document.readyState !== "loading") init();
  else document.addEventListener("DOMContentLoaded", init);
})();
""".strip()
