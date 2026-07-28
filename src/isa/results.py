import hashlib, json, os
import pandas as pd

RESULT_COLUMNS = ["strategy_id", "run_date", "universe", "metric",
                  "value", "ci_low", "ci_high", "params_hash"]

def params_hash(params):
    blob = json.dumps(params, sort_keys=True, default=str).encode()
    return hashlib.sha1(blob).hexdigest()[:12]

def _runs_path(root):
    return os.path.join(root, "runs.parquet")

def append_result(strategy_id, run_date, universe, metrics, cis, params, root="results"):
    os.makedirs(root, exist_ok=True)
    ph = params_hash(params)
    rows = []
    for metric, value in metrics.items():
        lo, hi = cis.get(metric, (None, None))
        rows.append({"strategy_id": strategy_id, "run_date": run_date,
                     "universe": universe, "metric": metric, "value": value,
                     "ci_low": lo, "ci_high": hi, "params_hash": ph})
    new = pd.DataFrame(rows, columns=RESULT_COLUMNS)
    path = _runs_path(root)
    if os.path.exists(path):
        new = pd.concat([pd.read_parquet(path), new], ignore_index=True)
    new.to_parquet(path, index=False)

def save_equity_curve(strategy_id, universe, equity, root="results"):
    folder = os.path.join(root, "equity_curves")
    os.makedirs(folder, exist_ok=True)
    safe = universe.replace(":", "_")
    path = os.path.join(folder, f"{strategy_id}__{safe}.parquet")
    equity.rename("equity").to_frame().to_parquet(path)
    return path

def load_results(root="results"):
    path = _runs_path(root)
    if not os.path.exists(path):
        return pd.DataFrame(columns=RESULT_COLUMNS)
    return pd.read_parquet(path)
