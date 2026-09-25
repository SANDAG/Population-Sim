from pyspark import pipelines as dp

source_root = spark.conf.get("popsim.source_root")


@dp.table(
    comment="Raw per-run metadata (config values) written by datalake_exporter",
    table_properties={"delta.feature.timestampNtz": "supported"},
)
def bronze_run_metadata():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "parquet")
        .load(f"{source_root}/run_metadata/")
    )
