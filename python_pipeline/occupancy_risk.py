from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

from common import OUT, occupancy, read

ROOT = Path(__file__).resolve().parent.parent


def main():
    c = occupancy(read("passenger_counts.csv"))
    if c.empty:
        return
    c["service_date"] = pd.to_datetime(c["service_date"], errors="coerce")
    c["event_time"] = pd.to_datetime(
        c.get("event_time", c["service_date"]), errors="coerce"
    )
    c = c.sort_values(["service_date", "count_id"]).reset_index(drop=True)
    c["risk_label"] = (c["occupancy_pct"] >= 0.95).astype(int)
    c["day_of_week"] = c.service_date.dt.dayofweek
    c["month"] = c.service_date.dt.month
    c["hour"] = c.event_time.dt.hour
    c["route_num"] = c.route_id.str.extract(r"(\d+)").astype(float)
    c["stop_num"] = c.stop_id.str.extract(r"(\d+)").astype(float)
    c["stop_sequence"] = pd.to_numeric(c.get("stop_sequence", 1), errors="coerce")

    features = [
        "capacity",
        "boarding",
        "alighting",
        "route_num",
        "stop_num",
        "day_of_week",
        "month",
        "hour",
        "stop_sequence",
        "route_train_rate",
    ]
    cut = max(1, int(len(c) * 0.80))
    train = c.iloc[:cut].copy()
    test = c.iloc[cut:].copy()
    route_rate = (
        train.groupby("route_id")["occupancy_pct"].mean().rename("route_train_rate")
    )
    train = train.merge(route_rate, on="route_id", how="left")
    test = test.merge(route_rate, on="route_id", how="left")
    train[features] = train[features].fillna(0)
    test[features] = test[features].fillna(0)

    model = RandomForestClassifier(
        n_estimators=30,
        max_depth=12,
        random_state=42,
        class_weight="balanced_subsample",
        n_jobs=-1,
        min_samples_leaf=3,
    )
    model.fit(train[features], train.risk_label)
    pred = model.predict(test[features])
    metrics = {
        "accuracy": accuracy_score(test.risk_label, pred),
        "precision": precision_score(test.risk_label, pred, zero_division=0),
        "recall": recall_score(test.risk_label, pred, zero_division=0),
        "f1": f1_score(test.risk_label, pred, zero_division=0),
        "train_rows": len(train),
        "test_rows": len(test),
        "features": ", ".join(features),
    }
    pd.DataFrame([metrics]).to_csv(
        Path(OUT) / "occupancy_risk_metrics.csv", index=False
    )
    result = test[
        ["count_id", "route_id", "stop_id", "service_date", "risk_label"]
    ].copy()
    result["predicted_risk"] = pred
    result.to_csv(Path(OUT) / "occupancy_risk_predictions.csv", index=False)
    joblib.dump(model, ROOT / "models" / "occupancy_risk_model.joblib")
    print(metrics)


if __name__ == "__main__":
    main()
