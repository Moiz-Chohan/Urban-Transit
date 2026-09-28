from pathlib import Path

from pyspark.sql import SparkSession, functions as F

ROOT = Path(__file__).resolve().parents[1]
PARQUET = ROOT / "parquet_data"


def main():
    spark = SparkSession.builder.appName("UrbanTransitIQ-SparkSQL").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    features = spark.read.parquet(str(PARQUET / "features"))
    features.createOrReplaceTempView("transport_features")
    result = spark.sql("""
        SELECT route_id,
               COUNT(*) AS records,
               ROUND(SUM(passenger_count), 2) AS total_passengers,
               ROUND(AVG(passenger_count), 2) AS avg_demand,
               ROUND(AVG(occupancy_pct) * 100, 2) AS avg_occupancy_pct,
               ROUND(AVG(CASE WHEN occupancy_pct >= 0.95 THEN 1 ELSE 0 END) * 100, 2) AS overcrowding_rate_pct
        FROM transport_features
        GROUP BY route_id
        ORDER BY avg_demand DESC
        """)
    result.show(20, truncate=False)
    result.write.mode("overwrite").option("header", True).csv(
        str(PARQUET / "spark_sql_route_summary")
    )
    spark.stop()


if __name__ == "__main__":
    main()
