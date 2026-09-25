from pyspark import pipelines as dp

source_root = spark.conf.get("popsim.source_root")


@dp.table(
    comment="Raw synthetic persons ingested from PopSim output",
    table_properties={"delta.feature.timestampNtz": "supported"},
)
def bronze_synthetic_persons():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "parquet")
        .load(f"{source_root}/synthetic_persons/")
    )
