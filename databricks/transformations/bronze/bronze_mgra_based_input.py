from pyspark import pipelines as dp

source_root = spark.conf.get("popsim.source_root")


@dp.table(
    comment=(
        "Raw E&F mgrabase for the run year (E&F staging mgrabase table, filtered to "
        "increment = year with selected columns; emp_tot renamed emp_total), exported "
        "with each PopSim run as the ABM team's MGRA-based input; not computed by PopSim"
    ),
    table_properties={"delta.feature.timestampNtz": "supported"},
)
def bronze_mgra_based_input():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "parquet")
        .load(f"{source_root}/mgra15_based_input/")
    )
