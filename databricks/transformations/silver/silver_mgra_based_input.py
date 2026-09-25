from pyspark import pipelines as dp
from pyspark.sql import functions as F


@dp.table(
    comment="Cleaned MGRA-based ABM input with run_id attached",
    table_properties={"delta.feature.timestampNtz": "supported"},
)
def silver_mgra_based_input():
    lookup = spark.read.table("run_id_lookup")
    return (
        spark.readStream.table("bronze_mgra_based_input")
        .drop("_rescued_data")
        .withColumn("year", F.col("year").cast("int"))
        .join(lookup, ["run_timestamp", "year"], "left")
        .transform(lambda df: df.select(
            "run_id",
            *[c for c in df.columns if c not in ("run_id", "run_timestamp")],
            "run_timestamp",
        ))
    )
