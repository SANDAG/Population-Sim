from pyspark import pipelines as dp

source_root = spark.conf.get("popsim.source_root")


@dp.table(
    comment="Raw MGRA-based ABM input file produced after PopSim synthesis",
    table_properties={"delta.feature.timestampNtz": "supported"},
)
def bronze_mgra_based_input():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "parquet")
        .load(f"{source_root}/mgra15_based_input/")
    )
