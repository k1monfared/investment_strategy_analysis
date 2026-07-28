from isa import cli

def test_build_subcommand_runs(tmp_path):
    from isa import results
    rroot = str(tmp_path / "results")
    results.append_result("s1", "2026-07-27", "AAPL", {"sharpe": 1.0}, {}, {}, root=rroot)
    out = str(tmp_path / "site")
    rc = cli.main(["build", "--results-root", rroot, "--out-dir", out])
    assert rc == 0
    assert (tmp_path / "site" / "index.html").exists()

def test_unknown_command_returns_nonzero():
    assert cli.main(["nope"]) != 0
