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
  // Dollar cost averaging: contribute a fixed amount every `every` bars into the
  // portfolio index. The reported curve is money-weighted (value / cumulative
  // contributions) indexed to 100, so it is comparable to the 100-indexed lump-sum
  // curves. Buys more units when the level is low, fewer when it is high.
  function dcaEquity(spec, portfolio) {
    var lvl = portfolio.values;
    var every = (spec && spec.every) ? spec.every : 21;
    var units = 0, contrib = 0, out = [];
    for (var i = 0; i < lvl.length; i++) {
      var L = lvl[i];
      if (i % every === 0 && L > 0) { units += 1.0 / L; contrib += 1.0; }
      out.push(contrib > 0 ? (units * L / contrib) * 100.0 : 100.0);
    }
    return { dates: portfolio.dates, values: out };
  }

  function equityFor(spec, portfolio, fee) {
    if (spec && spec.type === "dca") return dcaEquity(spec, portfolio);
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