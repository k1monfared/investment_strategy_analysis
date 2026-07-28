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
    Promise.all([getJSON("data/manifest.json"), getJSON("data/strategies.json")])
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