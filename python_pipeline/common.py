import os, pandas as pd, numpy as np

ROOT = os.path.dirname(os.path.dirname(__file__))
RAW = os.path.join(ROOT, "raw_data")
OUT = os.path.join(ROOT, "processed_data")
PARQUET = os.path.join(ROOT, "parquet_data")


def read(name):
    p = os.path.join(OUT, name)
    p = p if os.path.exists(p) else os.path.join(RAW, name)
    return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()


def save(df, name):
    os.makedirs(OUT, exist_ok=True)
    df.to_csv(os.path.join(OUT, name), index=False)
    return df


def occupancy(df):
    x = df.copy()
    x["occupancy_pct"] = x["passenger_count"] / x["capacity"].replace(0, np.nan)
    return x
