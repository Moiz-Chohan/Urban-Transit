from pathlib import Path

from pyspark.sql import SparkSession, functions as F

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw_data"
PARQUET = ROOT / "parquet_data"


def main():
    spark = SparkSession.builder.appName("UrbanTransitIQ-Ingest").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    c = (
        spark.read.option("header", True)
        .option("inferSchema", True)
        .csv(str(RAW / "passenger_counts.csv"))
        .toDF(
            *[
                x.lower()
                for x in spark.read.option("header", True)
                .csv(str(RAW / "passenger_counts.csv"))
                .columns
            ]
        )
    )
    clean = (
        c.withColumn("passenger_count", F.col("passenger_count").cast("double"))
        .withColumn("capacity", F.col("capacity").cast("double"))
        .dropDuplicates(["count_id"])
        .filter(F.col("passenger_count") >= 0)
        .filter(F.col("capacity") > 0)
    )
    clean.write.mode("overwrite").partitionBy("route_id").parquet(
        str(PARQUET / "passenger_counts_clean")
    )
    print("Input rows:", c.count())
    print("Clean rows:", clean.count())
    spark.stop()


if __name__ == "__main__":
    main()
