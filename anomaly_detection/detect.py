from pathlib import Path
import pandas as pd, numpy as np

ROOT = Path(__file__).resolve().parents[1]


def run():
    p = ROOT / "processed_data/passenger_counts.csv"
    out = ROOT / "processed_data/anomalies.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    d["occupancy"] = d["passenger_count"] / d["capacity"].replace(0, np.nan)
    q1, q3 = d["passenger_count"].quantile([0.25, 0.75])
    iqr = q3 - q1
    d["anomaly_reason"] = np.select(
        [
            d["passenger_count"] < 0,
            d["occupancy"] > 1.2,
            d["passenger_count"] > q3 + 1.5 * iqr,
        ],
        ["negative_count", "impossible_occupancy", "demand_spike"],
        "normal",
    )
    d[d.anomaly_reason != "normal"].to_csv(out, index=False)
    print(out)


if __name__ == "__main__":
    run()
