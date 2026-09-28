from pathlib import Path

from pyspark.sql import SparkSession, Window, functions as F

ROOT = Path(__file__).resolve().parents[1]
PARQUET = ROOT / "parquet_data"


def main():
    spark = SparkSession.builder.appName("UrbanTransitIQ-Features").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    c = spark.read.parquet(str(PARQUET / "passenger_counts_clean"))
    w_route = Window.partitionBy("route_id").orderBy("service_date", "count_id")
    w_route_date = Window.partitionBy("route_id", "service_date")
    thresholds = c.groupBy("route_id").agg(
        F.percentile_approx("passenger_count", 0.90).alias("route_peak_threshold")
    )

    f = (
        c.join(thresholds, "route_id", "left")
        .withColumn("hour", F.hour(F.to_timestamp("event_time")))
        .withColumn("previous_route_demand", F.lag("passenger_count").over(w_route))
        .withColumn(
            "rolling_route_demand",
            F.avg("passenger_count").over(w_route.rowsBetween(-7, -1)),
        )
        .withColumn("daily_route_demand", F.sum("passenger_count").over(w_route_date))
        .withColumn("daily_route_records", F.count("count_id").over(w_route_date))
        .withColumn(
            "service_utilization",
            F.col("passenger_count") / F.when(F.col("capacity") > 0, F.col("capacity")),
        )
        .withColumn(
            "demand_pressure",
            F.when(F.col("occupancy_pct") >= 0.95, "Excess demand")
            .when(F.col("occupancy_pct") < 0.35, "Excess capacity")
            .otherwise("Balanced"),
        )
        .withColumn(
            "is_peak_demand",
            (F.col("passenger_count") >= F.col("route_peak_threshold")).cast("int"),
        )
    )
    f.write.mode("overwrite").partitionBy("route_id").parquet(str(PARQUET / "features"))
    spark.stop()
    print("Spark feature engineering completed.")


if __name__ == "__main__":
    main()
