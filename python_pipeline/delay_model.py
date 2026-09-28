from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw_data"
OUT = ROOT / "processed_data"


def main():
    df = pd.read_csv(RAW / "delays.csv")
    df.columns = df.columns.str.strip().str.lower()
    df["service_date"] = pd.to_datetime(df["service_date"], errors="coerce")
    df["delay_minutes"] = pd.to_numeric(df["delay_minutes"], errors="coerce")
    df = (
        df.dropna(subset=["service_date", "delay_minutes"])
        .sort_values("service_date")
        .reset_index(drop=True)
    )
    df["severity"] = pd.cut(
        df["delay_minutes"],
        [-np.inf, 5, 10, 20, np.inf],
        labels=["On Time", "Minor", "Moderate", "Severe"],
    ).astype(str)
    df["route_num"] = df.route_id.str.extract(r"(\d+)").astype(float)
    df["stop_num"] = df.stop_id.str.extract(r"(\d+)").astype(float)
    df["vehicle_num"] = df.vehicle_id.str.extract(r"(\d+)").astype(float)
    df["day_of_week"] = df.service_date.dt.dayofweek
    df["month"] = df.service_date.dt.month
    df["scheduled_departure"] = pd.to_datetime(
        df.get("scheduled_departure", df["service_date"]), errors="coerce"
    )
    df["hour"] = df.scheduled_departure.dt.hour
    # Historical route delay is shifted before calculating the rolling statistic.
    df["historical_route_delay"] = df.groupby("route_id")["delay_minutes"].transform(
        lambda s: s.shift(1).rolling(30, min_periods=1).mean()
    )
    features = [
        "route_num",
        "stop_num",
        "vehicle_num",
        "day_of_week",
        "month",
        "hour",
        "historical_route_delay",
    ]
    df[features] = df[features].fillna(0)
    cut = max(1, int(len(df) * 0.80))
    train, test = df.iloc[:cut], df.iloc[cut:]
    model = RandomForestClassifier(
        n_estimators=30,
        max_depth=12,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )
    model.fit(train[features], train.severity)
    pred = model.predict(test[features])
    metrics = {
        "accuracy": accuracy_score(test.severity, pred),
        "precision_macro": precision_score(
            test.severity, pred, average="macro", zero_division=0
        ),
        "recall_macro": recall_score(
            test.severity, pred, average="macro", zero_division=0
        ),
        "f1_macro": f1_score(test.severity, pred, average="macro", zero_division=0),
        "train_rows": len(train),
        "test_rows": len(test),
        "features": ", ".join(features),
    }
    OUT.mkdir(exist_ok=True)
    pd.DataFrame([metrics]).to_csv(OUT / "delay_model_metrics.csv", index=False)
    pd.DataFrame(
        {
            "delay_id": test.delay_id,
            "actual_severity": test.severity,
            "predicted_severity": pred,
        }
    ).to_csv(OUT / "delay_predictions.csv", index=False)
    joblib.dump(model, ROOT / "models" / "delay_model.joblib")
    print(metrics)


if __name__ == "__main__":
    main()
