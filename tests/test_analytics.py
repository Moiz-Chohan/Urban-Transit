from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent


def test_forecast_has_baseline_and_future_horizon():
    metrics = pd.read_csv(ROOT / "processed_data" / "demand_forecast_metrics.csv")
    assert "baseline_mae" in metrics.columns
    assert "model_mae" in metrics.columns
    assert int(metrics.loc[0, "forecast_horizon_days"]) >= 1


def test_occupancy_model_metrics_are_present():
    metrics = pd.read_csv(ROOT / "processed_data" / "occupancy_risk_metrics.csv")
    assert 0 <= float(metrics.loc[0, "accuracy"]) <= 1
    assert "f1" in metrics.columns
