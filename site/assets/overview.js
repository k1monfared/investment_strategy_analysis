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