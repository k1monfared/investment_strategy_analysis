import os
from isa import results, build_site

def test_comparison_table_pivots(tmp_path):
    root = str(tmp_path)
    results.append_result("s1", "2026-07-27", "AAPL",
                          {"sharpe": 1.0, "total_return": 0.2}, {}, {}, root=root)
    df = results.load_results(root=root)
    table = build_site.comparison_table(df)
    assert "sharpe" in table.columns and "total_return" in table.columns

def test_build_site_writes_html(tmp_path):
    root = str(tmp_path / "results")
    results.append_result("s1", "2026-07-27", "AAPL",
                          {"sharpe": 1.0}, {"sharpe": (0.5, 1.5)}, {}, root=root)
    out = str(tmp_path / "site")
    path = build_site.build_site(results_root=root, out_dir=out)
    assert os.path.exists(path)
    html = open(path, encoding="utf-8").read()
    assert "s1" in html
    # no emojis in output
    assert all(ord(ch) < 0x1F000 for ch in html)
