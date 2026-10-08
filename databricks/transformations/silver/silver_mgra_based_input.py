from pyspark import pipelines as dp
from pyspark.sql import functions as F

from utilities.column_comments import (
    MGRA_BASED_INPUT,
    MGRA_BASED_INPUT_TYPES,
    schema_ddl,
)


@dp.table(
    comment=(
        "E&F mgrabase for the run year, exported with each PopSim run as the ABM "
        "team's MGRA-based input; bronze_mgra_based_input with run_id attached"
    ),
    schema=schema_ddl(MGRA_BASED_INPUT_TYPES, MGRA_BASED_INPUT),
    table_properties={"delta.feature.timestampNtz": "supported"},
)
# Data quality: drop rows with no run_id, i.e. from a partial export whose
# synthetic_persons never landed, so it never got a run_id_lookup entry
@dp.expect_or_drop("valid_run_id", "run_id IS NOT NULL")
def silver_mgra_based_input():
    lookup = spark.read.table("run_id_lookup")
    return (
        spark.readStream.table("bronze_mgra_based_input")
        .withColumn("year", F.col("year").cast("int"))
        .join(lookup, ["run_timestamp", "year"], "left")
        # Explicit column list and casts so the table matches its declared schema
        .select(*[
            c if c == "run_timestamp" else F.col(c).cast(t).alias(c)
            for c, t in MGRA_BASED_INPUT_TYPES
        ])
    )
