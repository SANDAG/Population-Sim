from pyspark import pipelines as dp
from pyspark.sql import functions as F

from utilities.column_comments import SEED_PERSON_TYPES, SEED_PERSONS, schema_ddl


@dp.table(
    comment="Cleaned seed persons across the household and GQ runs, unioned",
    schema=schema_ddl(SEED_PERSON_TYPES, SEED_PERSONS),
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

    return (
        combined
        .transform(lambda df: df.select(
            "run_id",
            *[c for c in df.columns if c not in ("run_id", "run_timestamp")],
            "run_timestamp",
        ))
        # Integer PUMS columns with nulls arrive as DOUBLE from the parquet
        .withColumns({
            "SPORDER": F.col("SPORDER").cast("int"),
            "AGEP": F.col("AGEP").cast("int"),
            "ESR": F.col("ESR").cast("int"),
            "COW": F.col("COW").cast("int"),
            "WKHP": F.col("WKHP").cast("int"),
            "MIL": F.col("MIL").cast("int"),
            "SCHL": F.col("SCHL").cast("int"),
            "OCCP": F.col("OCCP").cast("int"),
            "WKW": F.col("WKW").cast("int"),
            "SOC2": F.col("SOC2").cast("int"),
            "PINCP": F.col("PINCP").cast("int"),
        })
    )
