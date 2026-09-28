import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw_data"


def run(command, label):
    print(f"\n>>> {label}", flush=True)
    print(" ".join(str(x) for x in command), flush=True)
    env = None
    if any("spark-submit" in str(part).lower() for part in command):
        env = dict(**__import__("os").environ)
        env["PYSPARK_PYTHON"] = sys.executable
        env["PYSPARK_DRIVER_PYTHON"] = sys.executable
    subprocess.run(command, cwd=ROOT, check=True, env=env)


def dataset_ready():
    required = [
        ("tickets.csv", 2_000_000),
        ("passenger_counts.csv", 500_000),
        ("delays.csv", 250_000),
        ("routes.csv", 100),
        ("stops.csv", 500),
        ("vehicles.csv", 250),
        ("passengers.csv", 50_000),
        ("trips.csv", 250_000),
    ]
    for name, minimum in required:
        path = RAW / name
        if not path.exists():
            return False
        with path.open("rb") as handle:
            rows = sum(1 for _ in handle) - 1
        if rows < minimum:
            return False
    return True


def spark_submit_path():
    candidates = [
        shutil.which("spark-submit"),
        shutil.which("spark-submit.cmd"),
        str(ROOT / ".venv" / "Scripts" / "spark-submit.cmd"),
        str(ROOT / ".venv" / "Scripts" / "spark-submit"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--regenerate", action="store_true", help="Regenerate the competition dataset")
    args = parser.parse_args()

    if args.regenerate or not dataset_ready():
        run([sys.executable, "data_generator/generate_dataset.py", "--size", "competition"], "Generate competition dataset")
    else:
        print("\n>>> Existing competition dataset found; generation skipped.")

    run([sys.executable, "spark_jobs/data_quality.py"], "Run data-quality audit")
    run([sys.executable, "python_pipeline/run_pipeline.py"], "Run independent Python pipeline")
    run([sys.executable, "recommendation_engine/engine.py"], "Generate recommendations")

    spark = spark_submit_path()
    if spark:
        run([spark, "spark_jobs/process_transport.py"], "Spark ingestion, cleaning, joins and Parquet")
        run([spark, "spark_jobs/feature_engineering.py"], "Spark feature engineering")
        run([spark, "spark_jobs/analytics.py"], "Spark SQL / route analytics")
        run([spark, "spark_jobs/ml_models.py"], "Spark MLlib model evaluation")
        run([sys.executable, "dual_pipeline/compare_models.py"], "Spark vs Python comparison")
    else:
        status = ROOT / "processed_data" / "spark_status.txt"
        status.write_text(
            "Spark was not found during this run. No Spark metrics were fabricated.\n"
            "Install/configure Hadoop + Spark + PySpark and run run_all.py again.\n",
            encoding="utf-8",
        )
        print("\nSpark not found: Python workflow completed; Spark steps were skipped safely.")

    run([sys.executable, "reports/generate_reports.py"], "Generate reports")
    print("\nUrbanTransit IQ workflow finished.")
    print("Start backend: python backend\\app.py")
    print("Start frontend: cd frontend; npm install; npm run dev")


if __name__ == "__main__":
    main()
