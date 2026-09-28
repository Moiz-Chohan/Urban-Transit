from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "processed_data"


def main():
    spark_path = OUT / "spark_occupancy_predictions.csv"
    python_path = OUT / "occupancy_risk_predictions.csv"
    if not spark_path.exists() or not python_path.exists():
        print("Dual comparison skipped: run Spark MLlib and Python pipeline first.")
        return False

    spark = pd.read_csv(spark_path)
    python = pd.read_csv(python_path)
    comparison = spark.merge(
        python[["count_id", "risk_label", "predicted_risk"]],
        on="count_id",
        how="inner",
    ).head(500)
    if comparison.empty:
        print("Dual comparison skipped: no common unseen cases.")
        return False

    comparison["spark_prediction"] = comparison["spark_predicted_risk"].astype(int)
    comparison["python_prediction"] = comparison["predicted_risk"].astype(int)
    comparison["match"] = (
        comparison["spark_prediction"] == comparison["python_prediction"]
    )
    comparison["prediction_difference"] = (
        comparison["spark_prediction"] - comparison["python_prediction"]
    ).abs()
    comparison.to_csv(OUT / "dual_comparison.csv", index=False)

    summary = pd.DataFrame(
        [
            {
                "cases_compared": len(comparison),
                "agreement_rate": comparison["match"].mean(),
                "disagreement_rate": (~comparison["match"]).mean(),
                "spark_model": "Spark MLlib RandomForestClassifier",
                "python_model": "scikit-learn RandomForestClassifier",
            }
        ]
    )
    summary.to_csv(OUT / "dual_comparison_summary.csv", index=False)
    print(summary.to_string(index=False))
    return True


if __name__ == "__main__":
    main()
