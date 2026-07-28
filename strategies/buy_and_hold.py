META = {"id": "buy_and_hold", "name": "Buy and Hold",
        "kind": "benchmark", "params": {}}

def generate(prices, params):
    return {"tickers": list(prices.columns)}
