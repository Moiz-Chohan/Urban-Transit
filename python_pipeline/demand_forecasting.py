from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from common import OUT, read


def main(future_days=14):
    c = read("passenger_counts.csv")
    if c.empty:
        return
    c["service_date"] = pd.to_datetime(c["service_date"], errors="coerce")
    daily = (
        c.groupby("service_date", as_index=False)
        .passenger_count.sum()
        .sort_values("service_date")
    )
    daily = daily.set_index("service_date").asfreq("D", fill_value=0).reset_index()
    daily["day_of_week"] = daily.service_date.dt.dayofweek
    daily["month"] = daily.service_date.dt.month
    daily["trend"] = np.arange(len(daily))
    daily["lag_1"] = daily.passenger_count.shift(1)
    daily["lag_7"] = daily.passenger_count.shift(7)
    daily["rolling_7"] = daily.passenger_count.shift(1).rolling(7, min_periods=3).mean()
    daily = daily.dropna().reset_index(drop=True)
    features = ["day_of_week", "month", "trend", "lag_1", "lag_7", "rolling_7"]
    split = max(1, int(len(daily) * 0.80))
    train, test = daily.iloc[:split], daily.iloc[split:]
    model = RandomForestRegressor(
        n_estimators=160, random_state=42, n_jobs=-1, min_samples_leaf=2
    )
    model.fit(train[features], train.passenger_count)
    pred = model.predict(test[features])
    baseline = test["lag_1"]
    metrics = {
        "model_mae": float(mean_absolute_error(test.passenger_count, pred)),
        "model_rmse": float(mean_squared_error(test.passenger_count, pred) ** 0.5),
        "model_r2": float(r2_score(test.passenger_count, pred)),
        "baseline_mae": float(mean_absolute_error(test.passenger_count, baseline)),
        "baseline_rmse": float(
            mean_squared_error(test.passenger_count, baseline) ** 0.5
        ),
        "baseline_method": "previous-day (lag_1)",
        "train_days": len(train),
        "test_days": len(test),
        "forecast_horizon_days": future_days,
    }
    pd.DataFrame([metrics]).to_csv(
        Path(OUT) / "demand_forecast_metrics.csv", index=False
    )
    joblib.dump(
        model,
        Path(__file__).resolve().parents[1] / "models" / "demand_forecast_model.joblib",
    )
    pd.DataFrame(
        {
            "date": test.service_date,
            "actual": test.passenger_count,
            "prediction": pred,
            "baseline_lag1": baseline,
        }
    ).to_csv(Path(OUT) / "demand_forecast_predictions.csv", index=False)

    history = daily.copy()
    future_rows = []
    for _ in range(future_days):
        next_date = history.service_date.max() + pd.Timedelta(days=1)
        row = {
            "service_date": next_date,
            "day_of_week": next_date.dayofweek,
            "month": next_date.month,
            "trend": len(history),
            "lag_1": history.passenger_count.iloc[-1],
            "lag_7": (
                history.passenger_count.iloc[-7]
                if len(history) >= 7
                else history.passenger_count.mean()
            ),
            "rolling_7": history.passenger_count.iloc[-7:].mean(),
        }
        prediction = float(model.predict(pd.DataFrame([row])[features])[0])
        row["passenger_count"] = prediction
        history = pd.concat([history, pd.DataFrame([row])], ignore_index=True)
        future_rows.append({"date": next_date, "forecast": prediction})
    pd.DataFrame(future_rows).to_csv(
        Path(OUT) / "demand_future_forecast.csv", index=False
    )
    print(metrics)


if __name__ == "__main__":
    main()
