from pyspark import pipelines as dp
from pyspark.sql import functions as F


@dp.table(
    comment="Cleaned seed persons across the household and GQ runs, unioned",
    table_properties={"delta.feature.timestampNtz": "supported"},
)
def silver_seed_persons():
    lookup = spark.read.table("run_id_lookup")
    sources = [
        "bronze_seed_persons",
        "bronze_seed_persons_gq_mil",
        "bronze_seed_persons_gq_col",
        "bronze_seed_persons_gq_oth",
    ]

    def _clean(table_name):
        return (
            spark.readStream.table(table_name)
            .drop("_rescued_data")
            .withColumn("year", F.col("year").cast("int"))
            .join(lookup, ["run_timestamp", "year"], "left")
        )

    combined = _clean(sources[0])
    for table_name in sources[1:]:
        combined = combined.unionByName(_clean(table_name))

    return combined.transform(lambda df: df.select(
        "run_id",
        *[c for c in df.columns if c not in ("run_id", "run_timestamp")],
        "run_timestamp",
    ))
