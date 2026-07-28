(function () {
  "use strict";

  var DATA = "data/";
  var priceCache = {};
  var manifest = null;
  var strategies = [];

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
  // Each ticker is normalized to 100 at the first common date, then combined by
  // its share of total weight. Returns {dates:[...], values:[...]}.
  function buildPortfolio(selected) {
    // selected: [{ticker, weight, data:{d:[],c:[]}}]
    // find common date intersection
    var sets = selected.map(function (s) {
      var m = {};
      var d = s.data.d, c = s.data.c;
      for (var i = 0; i < d.length; i++) m[d[i]] = c[i];
      return m;
    });
    var base = selected[0].data.d;
    var common = [];
    for (var i = 0; i < base.length; i++) {
      var dt = base[i];
      var ok = true;
      for (var j = 0; j < sets.length; j++) {
        if (sets[j][dt] === undefined) { ok = false; break; }
      }
      if (ok) common.push(dt);
    }
    if (common.length === 0) return { dates: [], values: [] };

    var totalW = selected.reduce(function (a, s) { return a + s.weight; }, 0);
    if (totalW === 0) totalW = 1;

    // normalization factor per ticker: 100 / firstCommonPrice
    var norm = sets.map(function (m) { return 100.0 / m[common[0]]; });
    var values = [];
    for (var k = 0; k < common.length; k++) {
      var dt2 = common[k];
      var v = 0;
      for (var j2 = 0; j2 < sets.length; j2++) {
        var normedPrice = sets[j2][dt2] * norm[j2];
        v += (selected[j2].weight / totalW) * normedPrice;
      }
      values.push(v);
    }
    return { dates: common, values: values };
  }

  // ---- smoothing ----
  function resampleLast(series, mode) {
    // series: {dates:[YYYY-MM-DD], values:[]}; mode: 'D','W','M'
    if (mode === "D") return series;
    var out = { dates: [], values: [] };
    var lastKey = null, lastIdx = -1;
    for (var i = 0; i < series.dates.length; i++) {
      var d = series.dates[i];
      var key;
      if (mode === "M") key = d.slice(0, 7);
      else { // weekly: ISO-ish year+week bucket
        key = weekKey(d);
      }
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
    var day = (dt.getUTCDay() + 6) % 7; // Monday=0
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
  // Mirrors the Python engine closely enough for interactive exploration:
  // position is applied on the next bar, simple compounding, no fees by default.
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
      var held = pos[i - 1]; // enter next bar
      var r = held * rets[i];
      // fee when position changes
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
    return { total: total, cagr: cagr, sharpe: sharpe, mdd: mdd };
  }

  // ---- DOM wiring ----
  function selectedTickers() {
    var rows = document.querySelectorAll("#picker .row");
    var out = [];
    rows.forEach(function (row) {
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
    var rows = document.querySelectorAll("#stratlist .row");
    var out = [];
    rows.forEach(function (row) {
      var cb = row.querySelector("input[type=checkbox]");
      if (cb.checked) out.push(cb.value);
    });
    return out;
  }
  function currentSmoothing() {
    var mode = document.getElementById("smoothing").value;
    var win = parseInt(document.getElementById("rollwin").value, 10);
    return { mode: mode, win: win };
  }
  function applySmoothing(series) {
    var s = currentSmoothing();
    var out = series;
    if (s.mode === "R") out = rollingMean(series, s.win);
    else out = resampleLast(series, s.mode);
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
      title: "Portfolio value (indexed to 100 at start)",
      xaxis: { title: "" }, yaxis: { title: "Index" },
      hovermode: "x unified", showlegend: true
    };
    Plotly.newPlot("priceChart", [trace], layout, { responsive: true, displayModeBar: false });
  }

  function renderStrategyChart(portfolioRaw, stratIds) {
    var fee = parseFloat(document.getElementById("fee").value);
    if (isNaN(fee)) fee = 0;
    var traces = [];
    var baseline = equityFor({ type: "buy_and_hold" }, portfolioRaw, 0);
    traces.push({ x: baseline.dates, y: baseline.values, type: "scatter", mode: "lines",
      name: "Buy and hold (baseline)", line: { color: "#a0aec0", width: 2, dash: "dot" } });

    var rows = [];
    rows.push(rowMetrics("Buy and hold (baseline)", metrics(baseline)));

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

    document.getElementById("stratMetrics").innerHTML =
      "<table class='data'><thead><tr><th>Strategy</th><th>Total return</th>" +
      "<th>CAGR</th><th>Sharpe</th><th>Max drawdown</th></tr></thead><tbody>" +
      rows.join("") + "</tbody></table>";
  }
  function rowMetrics(name, m) {
    function cls(x) { return x >= 0 ? "metric-pos" : "metric-neg"; }
    return "<tr><td>" + name + "</td>" +
      "<td class='" + cls(m.total) + "'>" + fmtPct(m.total) + "</td>" +
      "<td class='" + cls(m.cagr) + "'>" + fmtPct(m.cagr) + "</td>" +
      "<td>" + fmtNum(m.sharpe) + "</td>" +
      "<td class='metric-neg'>" + fmtPct(m.mdd) + "</td></tr>";
  }

  function update() {
    var sel = selectedTickers();
    var status = document.getElementById("status");
    if (sel.length === 0) {
      status.textContent = "Select at least one ticker to build a portfolio.";
      document.getElementById("priceChart").innerHTML = "";
      document.getElementById("stratChart").innerHTML = "";
      document.getElementById("stratMetrics").innerHTML = "";
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
        status.textContent = "Selected tickers have no overlapping dates.";
        return;
      }
      status.textContent = sel.length + " tickers, " + portfolio.dates.length +
        " common trading days (" + portfolio.dates[0] + " to " +
        portfolio.dates[portfolio.dates.length - 1] + ").";
      renderPortfolioChart(portfolio);
      var strats = selectedStrategies();
      if (strats.length > 0) renderStrategyChart(portfolio, strats);
      else {
        document.getElementById("stratChart").innerHTML =
          "<p class='empty'>Select one or more strategies to compare them on this portfolio.</p>";
        document.getElementById("stratMetrics").innerHTML = "";
      }
    }).catch(function (e) {
      status.textContent = "Error: " + e.message;
    });
  }

  function buildPicker() {
    var bySector = {};
    manifest.tickers.forEach(function (t) {
      var s = t.s || "Uncategorized";
      (bySector[s] = bySector[s] || []).push(t.t);
    });
    var sectors = Object.keys(bySector).sort();
    var html = "";
    sectors.forEach(function (sec) {
      html += "<div class='sectorgroup' data-sector='" + sec.toLowerCase() + "'>";
      html += "<div class='sector'>" + sec + "</div>";
      bySector[sec].sort().forEach(function (tk) {
        html += "<div class='row' data-ticker='" + tk.toLowerCase() + "'>" +
          "<input type='checkbox' value='" + tk + "'>" +
          "<span class='tk'>" + tk + "</span>" +
          "<input type='number' min='0' step='0.1' value='1' disabled title='Relative weight'>" +
          "</div>";
      });
      html += "</div>";
    });
    document.getElementById("picker").innerHTML = html;

    document.querySelectorAll("#picker .row").forEach(function (row) {
      var cb = row.querySelector("input[type=checkbox]");
      var wt = row.querySelector("input[type=number]");
      cb.addEventListener("change", function () { wt.disabled = !cb.checked; });
    });
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
    document.getElementById("stratlist").innerHTML = html;
  }

  function wireControls() {
    document.getElementById("updateBtn").addEventListener("click", update);
    document.getElementById("clearBtn").addEventListener("click", function () {
      document.querySelectorAll("#picker input[type=checkbox]").forEach(function (cb) {
        cb.checked = false; cb.parentElement.querySelector("input[type=number]").disabled = true;
      });
      document.querySelectorAll("#stratlist input[type=checkbox]").forEach(function (cb) { cb.checked = false; });
      update();
    });
    document.getElementById("smoothing").addEventListener("change", function () {
      document.getElementById("rollwrap").style.display =
        this.value === "R" ? "block" : "none";
      update();
    });
    document.getElementById("rollwin").addEventListener("change", update);
    document.getElementById("fee").addEventListener("change", update);
    document.getElementById("search").addEventListener("input", function () {
      var q = this.value.trim().toLowerCase();
      document.querySelectorAll("#picker .sectorgroup").forEach(function (g) {
        var any = false;
        g.querySelectorAll(".row").forEach(function (r) {
          var show = !q || r.getAttribute("data-ticker").indexOf(q) === 0 ||
            r.getAttribute("data-ticker").indexOf(q) > -1;
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
        document.getElementById("status").textContent =
          manifest.tickers.length + " tickers available. Select some and press Update portfolio.";
      })
      .catch(function (e) {
        document.getElementById("status").textContent =
          "Could not load data files: " + e.message;
      });
  }

  if (document.readyState !== "loading") init();
  else document.addEventListener("DOMContentLoaded", init);
})();