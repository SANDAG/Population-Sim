from pyspark import pipelines as dp
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from utilities.column_comments import (
    SYNTHETIC_HOUSEHOLD_RENAMES,
    SYNTHETIC_HOUSEHOLD_TYPES,
    SYNTHETIC_HOUSEHOLDS,
    schema_ddl,
)


def process_household(households: DataFrame, xref_taz_mgra: DataFrame) -> DataFrame:
    """Add ABM3 household fields using the 2022 ASPE poverty guidelines."""
    poverty_guideline = F.when(
        F.col("persons") >= 2,
        F.lit(13590) + F.lit(4720) * (F.col("persons") - 1),
    ).otherwise(F.lit(13590))
    households = households.join(xref_taz_mgra, ["run_id", "mgra"], "inner")
    households = households.withColumns({
        "household_serial_no": F.lit(0),
        "hinc": F.coalesce(F.col("hinc"), F.lit(0)),
        "num_workers": F.coalesce(F.col("num_workers"), F.lit(0)).cast("int"),
        "veh": F.coalesce(F.col("veh"), F.lit(0)).cast("int"),
        "unittype": F.when(F.col("gq_type").isin(1, 2, 3), 1)
            .otherwise(F.col("gq_type")).cast("int"),
        "version": F.lit(0),
        "poverty": F.col("hinc") / poverty_guideline,
    })
    return households.withColumn(
        "hinccat1",
        F.when(F.col("hinc") < 30000, 1)
        .when(F.col("hinc") < 60000, 2)
        .when(F.col("hinc") < 100000, 3)
        .when(F.col("hinc") < 150000, 4)
        .otherwise(5),
    )


@dp.table(
    comment="Cleaned synthetic households with standardized columns and ABM3 household fields",
    schema=schema_ddl(SYNTHETIC_HOUSEHOLD_TYPES, SYNTHETIC_HOUSEHOLDS),
    table_properties={"delta.feature.timestampNtz": "supported"},
)
@dp.expect_or_drop("valid_household_id", "hhid IS NOT NULL")
@dp.expect_or_drop("valid_mgra", "mgra IS NOT NULL")
# Data quality: drop rows with no run_id, i.e. from a partial export whose
# synthetic_persons never landed, so it never got a run_id_lookup entry
@dp.expect_or_drop("valid_run_id", "run_id IS NOT NULL")
def silver_synthetic_households():
    lookup = spark.read.table("run_id_lookup")
    xref_taz_mgra = spark.read.table("silver_mgra_based_input").select(
        "run_id", "mgra", "taz",
    )
    households = (
        spark.readStream.table("bronze_synthetic_households")
        .drop("_rescued_data")
        .withColumn("year", F.col("year").cast("int"))
        .join(lookup, ["run_timestamp", "year"], "left")
        .transform(lambda df: df.select(
            "run_id",
            *[c for c in df.columns if c not in ("run_id", "run_timestamp")],
            "run_timestamp",
        ))
        .withColumnsRenamed(SYNTHETIC_HOUSEHOLD_RENAMES)
        .withColumns({
            "persons": F.col("persons").cast("int"),
            "hinc": F.col("hinc").cast("int"),
            "hht": F.col("hht").cast("int"),
            "presence_of_children": F.col("presence_of_children").cast("int"),
            "veh": F.col("veh").cast("int"),
            "bldgsz": F.col("bldgsz").cast("int"),
        })
    )
    return process_household(households, xref_taz_mgra).select(
        *[column for column, _ in SYNTHETIC_HOUSEHOLD_TYPES]
    )
