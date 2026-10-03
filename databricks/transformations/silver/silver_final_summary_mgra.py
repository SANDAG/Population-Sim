from pyspark import pipelines as dp
from pyspark.sql import functions as F


@dp.table(
    comment="Cleaned MGRA-level final summary with validated geography and id",
    table_properties={"delta.feature.timestampNtz": "supported"},
)
@dp.expect_or_drop("valid_id", "id IS NOT NULL")
def silver_final_summary_mgra():
    lookup = spark.read.table("run_id_lookup")
    return (
        spark.readStream.table("bronze_final_summary_mgra")
        .drop("_rescued_data")
        .withColumn("year", F.col("year").cast("int"))
        .join(lookup, ["run_timestamp", "year"], "left")
        .transform(lambda df: df.select(
            "run_id",
            *[c for c in df.columns if c not in ("run_id", "run_timestamp")],
            "run_timestamp",
        ))
    )
