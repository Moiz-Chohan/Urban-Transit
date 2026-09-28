from pathlib import Path

import pandas as pd
from pyspark.ml.evaluation import MulticlassClassificationEvaluator, RegressionEvaluator
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.regression import GBTRegressor, LinearRegression, RandomForestRegressor
from pyspark.sql import SparkSession, functions as F

ROOT = Path(__file__).resolve().parents[1]
PARQUET = ROOT / "parquet_data"
OUT = ROOT / "processed_data"
MODELS = ROOT / "models" / "spark"

FEATURES = [
    "route_num",
    "stop_num",
    "capacity",
    "boarding",
    "alighting",
    "day_num",
    "is_weekend",
    "previous_route_demand",
    "rolling_route_demand",
]


def prepare(spark):
    d = spark.read.parquet(str(PARQUET / "features")).fillna(0)
    return (
        d.withColumn(
            "route_num", F.regexp_extract("route_id", r"(\d+)", 1).cast("double")
        )
        .withColumn("stop_num", F.regexp_extract("stop_id", r"(\d+)", 1).cast("double"))
        .withColumn("day_num", F.dayofweek("service_date").cast("double"))
        .select("count_id", "passenger_count", "occupancy_pct", *FEATURES)
        .fillna(0)
    )


def main():
    spark = SparkSession.builder.appName("UrbanTransitIQ-SparkMLlib").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    d = prepare(spark)
    assembler = VectorAssembler(inputCols=FEATURES, outputCol="features")
    data = assembler.transform(d)
    train, test = data.randomSplit([0.8, 0.2], seed=42)
    train = train.cache()
    test = test.cache()

    regression_models = {
        "linear_regression": LinearRegression(
            featuresCol="features", labelCol="passenger_count"
        ),
        "random_forest": RandomForestRegressor(
            featuresCol="features", labelCol="passenger_count", numTrees=60, seed=42
        ),
        "gbt": GBTRegressor(
            featuresCol="features", labelCol="passenger_count", maxIter=40, seed=42
        ),
    }
    rows = []
    reg_eval = RegressionEvaluator(
        labelCol="passenger_count", predictionCol="prediction"
    )
    best_name = None
    best_rmse = float("inf")
    best_prediction = None

    for name, estimator in regression_models.items():
        model = estimator.fit(train)
        predicted = model.transform(test)
        rmse = reg_eval.evaluate(predicted, {"metricName": "rmse"})
        mae = reg_eval.evaluate(predicted, {"metricName": "mae"})
        rows.append(
            {
                "model": name,
                "task": "passenger_count_regression",
                "rmse": rmse,
                "mae": mae,
            }
        )
        model.write().overwrite().save(str(MODELS / name))
        if rmse < best_rmse:
            best_rmse = rmse
            best_name = name
            best_prediction = predicted

    classifier_data = data.withColumn(
        "label", (F.col("occupancy_pct") >= 0.95).cast("double")
    )
    ctrain, ctest = classifier_data.randomSplit([0.8, 0.2], seed=42)
    classifier = RandomForestClassifier(
        featuresCol="features",
        labelCol="label",
        predictionCol="prediction",
        numTrees=80,
        seed=42,
    )
    cmodel = classifier.fit(ctrain)
    cpred = cmodel.transform(ctest)
    f1 = MulticlassClassificationEvaluator(
        labelCol="label", predictionCol="prediction", metricName="f1"
    ).evaluate(cpred)
    accuracy = MulticlassClassificationEvaluator(
        labelCol="label", predictionCol="prediction", metricName="accuracy"
    ).evaluate(cpred)
    rows.append(
        {
            "model": "occupancy_random_forest",
            "task": "occupancy_classification",
            "f1": f1,
            "accuracy": accuracy,
        }
    )
    cmodel.write().overwrite().save(str(MODELS / "occupancy_random_forest"))

    OUT.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / "spark_model_metrics.csv", index=False)

    # A small, explicit unseen-case evidence set for the dual-pipeline comparison.
    if best_prediction is not None:
        best_prediction.select("count_id", "passenger_count", "prediction").limit(
            500
        ).toPandas().rename(
            columns={
                "passenger_count": "actual_passenger_count",
                "prediction": "spark_prediction",
            }
        ).to_csv(
            OUT / "spark_demand_predictions.csv", index=False
        )
    cpred.select("count_id", "label", "prediction").limit(500).toPandas().rename(
        columns={"label": "spark_risk_label", "prediction": "spark_predicted_risk"}
    ).to_csv(OUT / "spark_occupancy_predictions.csv", index=False)

    train.unpersist()
    test.unpersist()
    spark.stop()
    print(f"Spark MLlib complete. Best regression model: {best_name}")


if __name__ == "__main__":
    main()
