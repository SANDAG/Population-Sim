from pyspark import pipelines as dp
from pyspark.sql import functions as F


# Streaming table so each update only reads new bronze rows and each run is
# logged once, with the micro-batch it first arrived in (current_timestamp() is
# fixed per micro-batch). run_id_lookup numbers runs from this log, so
# reset.allowed=false keeps a full refresh from wiping it and renumbering ids
# that silver tables already reference.
@dp.table(
    comment="One row per PopSim run, with when the pipeline first ingested it; source for run_id_lookup",
    table_properties={
        "delta.feature.timestampNtz": "supported",
        "pipelines.reset.allowed": "false",
    },
)
def run_ingest_log():
    return (
        spark.readStream.table("bronze_synthetic_persons")
        .select(F.col("year").cast("int").alias("year"), "run_timestamp")
        .dropDuplicates(["run_timestamp", "year"])
        .withColumn("ingested_at", F.current_timestamp())
    )
