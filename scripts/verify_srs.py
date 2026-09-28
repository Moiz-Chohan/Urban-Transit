from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

required = [
    "README.md",
    "AI_USAGE.md",
    "requirements.txt",
    "LICENSE",
    "data_generator/generate_dataset.py",
    "spark_jobs/process_transport.py",
    "spark_jobs/feature_engineering.py",
    "spark_jobs/ml_models.py",
    "spark_jobs/analytics.py",
    "python_pipeline/run_pipeline.py",
    "python_pipeline/demand_forecasting.py",
    "python_pipeline/occupancy_risk.py",
    "python_pipeline/delay_model.py",
    "python_pipeline/route_clustering.py",
    "dual_pipeline/compare_models.py",
    "recommendation_engine/engine.py",
    "what_if/simulator.py",
    "backend/app.py",
    "frontend/package.json",
    "tests/test_project.py",
    "tests/test_analytics.py",
    "documentation/project_report.md",
    "documentation/technical_blog.md",
]
missing = [item for item in required if not (ROOT / item).exists()]
print(f"Implementation files present: {len(required) - len(missing)}/{len(required)}")
if missing:
    print("Missing:")
    for item in missing:
        print(" -", item)
    raise SystemExit(1)

print("Dataset and processed evidence files are checked by pytest.")
print(
    "External submission items still require team action: deployment, public repository, screenshots, demo video and final credentials."
)
