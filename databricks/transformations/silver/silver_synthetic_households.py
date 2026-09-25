from pyspark import pipelines as dp
from pyspark.sql import functions as F


@dp.table(
    comment="Cleaned synthetic households with standardized column names and types",
    table_properties={"delta.feature.timestampNtz": "supported"},
)
@dp.expect_or_drop("valid_household_id", "household_id IS NOT NULL")
@dp.expect_or_drop("valid_mgra", "mgra IS NOT NULL")
def silver_synthetic_households():
    lookup = spark.read.table("run_id_lookup")
    return (
        spark.readStream.table("bronze_synthetic_households")
        .drop("_rescued_data")
        .withColumn("year", F.col("year").cast("int"))
        .join(lookup, ["run_timestamp", "year"], "left")
        .transform(lambda df: df.select(
            "run_id",
            *[c for c in df.columns if c not in ("run_id", "run_timestamp")],
            "run_timestamp",
        ))
        .withColumnsRenamed({
            "SERIALNO": "serialno",
            "NP": "num_persons",
            "HHADJINC": "hh_adj_income",
            "HHT": "hh_type",
            "HUPAC": "presence_of_children",
            "VEH": "vehicles",
            "BLD": "building_type",
        })
        .withColumns({
            "num_persons": F.col("num_persons").cast("int"),
            "hh_adj_income": F.col("hh_adj_income").cast("int"),
            "hh_type": F.col("hh_type").cast("int"),
            "presence_of_children": F.col("presence_of_children").cast("int"),
            "vehicles": F.col("vehicles").cast("int"),
            "building_type": F.col("building_type").cast("int"),
        })
    )
