from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def build_od():
    p = ROOT / "processed_data/passenger_counts.csv"
    out = ROOT / "processed_data/od_matrix.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    if "origin_stop_id" not in d:
        d["origin_stop_id"] = d["stop_id"].shift(1).fillna(d["stop_id"]).astype(str)
    if "destination_stop_id" not in d:
        d["destination_stop_id"] = d["stop_id"].astype(str)
    cols = ["origin_stop_id", "destination_stop_id", "route_id"]
    x = (
        d.groupby(cols, as_index=False)["passenger_count"]
        .sum()
        .rename(columns={"passenger_count": "passenger_count"})
    )
    x.to_csv(out, index=False)
    print(out)


if __name__ == "__main__":
    build_od()
