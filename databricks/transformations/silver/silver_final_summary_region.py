from pyspark import pipelines as dp
from pyspark.sql import functions as F

from utilities.column_comments import (
    FINAL_SUMMARY_REGION,
    FINAL_SUMMARY_REGION_TYPES,
    FINAL_SUMMARY_REGION_WEIGHTS,
    schema_ddl,
)


@dp.table(
    comment=(
        "Region-wide control totals vs. weighted totals at each PopulationSim "
        "balancing stage (household synthesis run, i.e. people in households, "
        "excluding group quarters), one row per control; "
        "mgra_integer_weight is the final synthetic result"
    ),
    schema=schema_ddl(FINAL_SUMMARY_REGION_TYPES, FINAL_SUMMARY_REGION),
    table_properties={"delta.feature.timestampNtz": "supported"},
)
# Data quality: drop rows with no run_id, i.e. from a partial export whose
# synthetic_persons never landed, so it never got a run_id_lookup entry
@dp.expect_or_drop("valid_run_id", "run_id IS NOT NULL")
def silver_final_summary_region():
    lookup = spark.read.table("run_id_lookup")
    return (
        spark.readStream.table("bronze_final_summary_region")
        .withColumn("year", F.col("year").cast("int"))
        .join(lookup, ["run_timestamp", "year"], "left")
        # Explicit column list so the table matches its declared schema
        .select(
            "run_id",
            "year",
            "control_name",
            F.col("control_value").cast("double").alias("control_value"),
            *[F.col(c).cast("double").alias(c) for c in FINAL_SUMMARY_REGION_WEIGHTS],
            "run_timestamp",
        )
    )
