from pyspark import pipelines as dp

source_root = spark.conf.get("popsim.source_root")


@dp.table(
    comment="Raw PUMA-level final summary from the household PopSim run",
    table_properties={"delta.feature.timestampNtz": "supported"},
)
def bronze_final_summary_mgra_puma():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "parquet")
        .load(f"{source_root}/final_summary_mgra_PUMA/")
    )
