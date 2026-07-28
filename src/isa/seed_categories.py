import os
import pandas as pd

SECTOR_COLUMNS = ["ticker", "sector", "industry", "sic"]

def build_sectors(rows):
    df = pd.DataFrame(rows, columns=SECTOR_COLUMNS)
    df["ticker"] = df["ticker"].str.upper()
    return df.drop_duplicates("ticker", keep="last").reset_index(drop=True)

def build_membership(constituents):
    out = []
    for index_name, tickers in constituents.items():
        for t in tickers:
            out.append({"ticker": t.upper(), "index": index_name,
                        "start": "1990-01-01", "end": None})
    return pd.DataFrame(out, columns=["ticker", "index", "start", "end"])

def save_categories(sectors_df, membership_df, root="data/categories"):
    os.makedirs(root, exist_ok=True)
    sectors_df.to_parquet(os.path.join(root, "sectors.parquet"), index=False)
    membership_df.to_parquet(os.path.join(root, "membership.parquet"), index=False)

def _sp500_from_wikipedia():
    tables = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    t = tables[0]
    return [{"ticker": r["Symbol"], "sector": r["GICS Sector"],
             "industry": r["GICS Sub-Industry"], "sic": None}
            for _, r in t.iterrows()]

def main():
    rows = _sp500_from_wikipedia()
    sectors = build_sectors(rows)
    membership = build_membership({"sp500": sectors["ticker"].tolist()})
    save_categories(sectors, membership)
    print(f"seeded {len(sectors)} tickers")

if __name__ == "__main__":
    main()
