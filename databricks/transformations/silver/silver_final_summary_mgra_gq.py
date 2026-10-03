from pyspark import pipelines as dp
from pyspark.sql import functions as F


@dp.table(
    comment="Cleaned MGRA-level final summary for all GQ runs, unioned and tagged by synthesis_run",
    table_properties={"delta.feature.timestampNtz": "supported"},
)
@dp.expect_or_drop("valid_id", "id IS NOT NULL")
def silver_final_summary_mgra_gq():
    lookup = spark.read.table("run_id_lookup")
    sources = [
        "bronze_final_summary_mgra_gq_mil",
        "bronze_final_summary_mgra_gq_col",
        "bronze_final_summary_mgra_gq_oth",
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
