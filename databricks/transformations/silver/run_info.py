from pyspark import pipelines as dp
from pyspark.sql import functions as F


# Recomputed each update, but both inputs are one row per run so it's cheap, and
# older runs pick up any metadata columns added later.
@dp.materialized_view(
    comment="One row per PopSim run: run_id plus run-level metadata",
    table_properties={"delta.feature.timestampNtz": "supported"},
)
def run_info():
    metadata = (
        spark.read.table("bronze_run_metadata")
        .drop("_rescued_data")
        .withColumn("year", F.col("year").cast("int"))
    )
    return (
        spark.read.table("run_id_lookup")
        .join(metadata, ["run_timestamp", "year"], "left")
        .transform(lambda df: df.select(
            "run_id",
            *[c for c in df.columns if c not in ("run_id", "run_timestamp")],
            "run_timestamp",
        ))
    )
