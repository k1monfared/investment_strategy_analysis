import pandas as pd
from isa import strategy

def test_discovers_shipped_strategies():
    mods = strategy.discover_strategies("strategies")
    ids = {m.META["id"] for m in mods}
    assert {"ma_crossover", "buy_and_hold"} <= ids

def test_load_validates_meta(tmp_path):
    import pytest
    bad = tmp_path / "bad.py"
    bad.write_text("META = {'id': 'x'}\n")  # missing keys, no generate
    with pytest.raises(ValueError):
        strategy.load_strategy(str(bad))

def test_ma_crossover_generate_shape():
    mods = {m.META["id"]: m for m in strategy.discover_strategies("strategies")}
    px = pd.DataFrame({"AAPL": [1, 2, 3, 4, 5, 6]}, dtype=float)
    out = mods["ma_crossover"].generate(px, {"fast": 2, "slow": 3})
    assert set(out) == {"entries", "exits"}
    assert out["entries"].shape == px.shape

def test_buy_and_hold_kind():
    mods = {m.META["id"]: m for m in strategy.discover_strategies("strategies")}
    assert mods["buy_and_hold"].META["kind"] == "benchmark"
