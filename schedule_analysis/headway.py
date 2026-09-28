from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def run():
    p = ROOT / "processed_data/trips.csv"
    out = ROOT / "processed_data/headway_analysis.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    time_col = next(
        (
            c
            for c in ["actual_departure", "scheduled_departure", "departure_time"]
            if c in d
        ),
        None,
    )
    if not time_col:
        return
    d[time_col] = pd.to_datetime(d[time_col], errors="coerce")
    d = d.sort_values(["route_id", time_col])
    d["headway_minutes"] = (
        d.groupby("route_id")[time_col].diff().dt.total_seconds() / 60
    )
    d["bunching"] = d.headway_minutes < 5
    d["excessive_gap"] = d.headway_minutes > 30
    d.to_csv(out, index=False)
    print(out)


if __name__ == "__main__":
    run()
