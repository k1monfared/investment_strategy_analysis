META = {"id": "ma_crossover", "name": "Moving Average Crossover",
        "kind": "signal", "params": {"fast": 20, "slow": 50}}

def generate(prices, params):
    fast = prices.rolling(params["fast"]).mean()
    slow = prices.rolling(params["slow"]).mean()
    return {"entries": fast > slow, "exits": fast < slow}
