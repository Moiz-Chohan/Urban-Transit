from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent


def test_core_structure():
    required = [
        "backend/app.py",
        "data_generator/generate_dataset.py",
        "spark_jobs/process_transport.py",
        "spark_jobs/feature_engineering.py",
        "spark_jobs/ml_models.py",
        "python_pipeline/demand_forecasting.py",
        "python_pipeline/occupancy_risk.py",
        "dual_pipeline/compare_models.py",
        "frontend/package.json",
    ]
    assert all((ROOT / item).exists() for item in required)


def test_competition_dataset_scale():
    expected = {
        "tickets.csv": 2_000_000,
        "passenger_counts.csv": 500_000,
        "delays.csv": 250_000,
        "routes.csv": 100,
        "stops.csv": 500,
        "vehicles.csv": 250,
        "passengers.csv": 50_000,
    }
    for filename, minimum in expected.items():
        path = ROOT / "raw_data" / filename
        assert path.exists()
        rows = sum(1 for _ in path.open("rb")) - 1
        assert rows >= minimum, f"{filename}: {rows} < {minimum}"


def test_required_processed_outputs_have_rows():
    outputs = [
        "route_performance.csv",
        "peak_demand.csv",
        "persistent_overcrowding.csv",
        "underutilized_services.csv",
        "od_matrix.csv",
        "recommendations.csv",
    ]
    for filename in outputs:
        path = ROOT / "processed_data" / filename
        assert path.exists()
        assert len(pd.read_csv(path, nrows=2)) > 0
