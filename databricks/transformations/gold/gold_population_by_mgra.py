from pyspark import pipelines as dp
from pyspark.sql import functions as F


@dp.materialized_view(
    comment="Population demographics aggregated by MGRA and year"
)
def gold_population_by_mgra():
    return (
        spark.read.table("silver_synthetic_persons")
        .groupBy("run_id","mgra", "year")
        .agg(
            F.count("*").alias("total_population"),
            F.sum(F.when(F.col("sex") == 1, 1).otherwise(0)).alias("male_count"),
            F.sum(F.when(F.col("sex") == 2, 1).otherwise(0)).alias("female_count"),
            F.avg("age").alias("avg_age"),
            F.sum(F.when(F.col("age") < 18, 1).otherwise(0)).alias("under_18_count"),
            F.sum(F.when((F.col("age") >= 18) & (F.col("age") < 65), 1).otherwise(0)).alias("working_age_count"),
            F.sum(F.when(F.col("age") >= 65, 1).otherwise(0)).alias("senior_count"),
            F.sum(F.when(F.col("employment_status").isin(1, 2, 4, 5), 1).otherwise(0)).alias("employed_count"),
        )
    )
