import os, glob
import pandas as pd
import yaml

def load_sectors(root="data/categories"):
    return pd.read_parquet(os.path.join(root, "sectors.parquet"))

def load_membership(root="data/categories"):
    return pd.read_parquet(os.path.join(root, "membership.parquet"))

def load_theme(name, root="data/themes"):
    with open(os.path.join(root, f"{name}.yml")) as f:
        return list(yaml.safe_load(f)["tickers"])

def resolve_universe(spec, cat_root="data/categories", theme_root="data/themes", price_root="data/prices"):
    if spec == "all":
        return sorted(os.path.splitext(os.path.basename(p))[0]
                      for p in glob.glob(os.path.join(price_root, "*.parquet")))
    if spec.startswith("sector:"):
        name = spec.split(":", 1)[1]
        df = load_sectors(cat_root)
        return df.loc[df["sector"] == name, "ticker"].tolist()
    if spec.startswith("index:"):
        name = spec.split(":", 1)[1]
        df = load_membership(cat_root)
        return df.loc[df["index"] == name, "ticker"].tolist()
    if spec.startswith("theme:"):
        return load_theme(spec.split(":", 1)[1], theme_root)
    return [spec.upper()]
