from pyspark import pipelines as dp
from pyspark.sql import functions as F


@dp.materialized_view(
    comment="Household demographics aggregated by MGRA and year"
)
def gold_household_demographics():
    return (
        spark.read.table("silver_synthetic_households")
        .groupBy("run_id","mgra", "year")
        .agg(
            F.count("hhid").alias("total_households"),
            F.avg("persons").alias("avg_household_size"),
            F.avg("hinc").alias("avg_household_income"),
            F.sum(F.when(F.col("gq_type") == 0, 1).otherwise(0)).alias("non_gq_households"),
            F.sum(F.when(F.col("gq_type") > 0, 1).otherwise(0)).alias("gq_households"),
            F.avg("num_workers").alias("avg_workers_per_hh"),
        )
    )
