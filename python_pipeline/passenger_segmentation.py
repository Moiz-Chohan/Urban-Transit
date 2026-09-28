from pathlib import Path

import joblib
import pandas as pd
from sklearn.cluster import KMeans

from common import OUT, read, save

ROOT = Path(__file__).resolve().parents[1]


def main():
    tickets = read("tickets.csv")
    if tickets.empty:
        return
    x = (
        tickets.groupby("passenger_id")
        .agg(
            trips=("trip_id", "nunique"),
            tickets=("ticket_id", "count"),
            avg_fare=("fare", "mean"),
        )
        .reset_index()
    )
    model = KMeans(n_clusters=4, random_state=42, n_init=10)
    x["segment"] = model.fit_predict(x[["trips", "tickets", "avg_fare"]].fillna(0))
    save(x, "passenger_segments.csv")
    joblib.dump(model, ROOT / "models" / "passenger_segmentation_model.joblib")


if __name__ == "__main__":
    main()
