from pyspark import pipelines as dp

source_root = spark.conf.get("popsim.source_root")


@dp.table(
    comment="Raw synthetic persons ingested from PopSim output",
    # run_id_lookup (downstream) is reset-protected so it never renumbers ids
    # already referenced elsewhere; a reset here would delete the source data
    # it was built from, so this must be reset-protected too.
    table_properties={
        "delta.feature.timestampNtz": "supported",
        "pipelines.reset.allowed": "false",
    },
)
def bronze_synthetic_persons():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "parquet")
        .load(f"{source_root}/synthetic_persons/")
    )
