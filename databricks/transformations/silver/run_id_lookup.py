from pyspark import pipelines as dp
from pyspark.sql import functions as F


# Streaming table so each update only reads new bronze rows; run_id is assigned once
# on insert and never renumbered. reset.allowed=false keeps a full refresh from
# reassigning ids that silver tables already reference.
@dp.table(
    comment="One row per PopSim run: stable run_id assigned once at first ingestion",
    schema="""
        run_id BIGINT GENERATED ALWAYS AS IDENTITY,
        year INT,
        run_timestamp TIMESTAMP_NTZ
    """,
    table_properties={
        "delta.feature.timestampNtz": "supported",
        "pipelines.reset.allowed": "false",
    },
)
def run_id_lookup():
    return (
        spark.readStream.table("bronze_synthetic_persons")
        .select(F.col("year").cast("int").alias("year"), "run_timestamp")
        .dropDuplicates(["run_timestamp", "year"])
        # Single writer task so identity values come out consecutive instead of
        # jumping between per-task ranges after the dropDuplicates shuffle.
        .coalesce(1)
    )
