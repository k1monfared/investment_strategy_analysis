import pandas as pd
from isa import results

def test_params_hash_stable():
    assert results.params_hash({"a": 1, "b": 2}) == results.params_hash({"b": 2, "a": 1})

def test_append_and_load(tmp_path):
    root = str(tmp_path)
    results.append_result("ma_crossover", "2026-07-27", "index:sp500",
                          metrics={"sharpe": 1.2, "total_return": 0.4},
                          cis={"sharpe": (0.8, 1.6)}, params={"fast": 20}, root=root)
    df = results.load_results(root=root)
    assert set(df.columns) == set(results.RESULT_COLUMNS)
    sharpe_row = df[df["metric"] == "sharpe"].iloc[0]
    assert sharpe_row["value"] == 1.2
    assert sharpe_row["ci_low"] == 0.8 and sharpe_row["ci_high"] == 1.6
    tr_row = df[df["metric"] == "total_return"].iloc[0]
    assert pd.isna(tr_row["ci_low"])  # no CI provided

def test_append_is_cumulative(tmp_path):
    root = str(tmp_path)
    for d in ["2026-07-26", "2026-07-27"]:
        results.append_result("s", d, "AAPL", {"sharpe": 1.0}, {}, {}, root=root)
    assert len(results.load_results(root=root)) == 2

def test_save_equity_curve(tmp_path):
    root = str(tmp_path)
    s = pd.Series([1.0, 1.1], index=pd.to_datetime(["2024-01-02", "2024-01-03"]))
    p = results.save_equity_curve("s", "AAPL", s, root=root)
    assert p.endswith(".parquet")
