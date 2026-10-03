from pyspark import pipelines as dp
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# GQ runs each define a single "Total_GQ" target — the same string reused
# across all three types (see populationsim/configs_gq_*/controls.csv) — so
# control_id must be ordered by a stable per-run priority (household first,
# then GQ types in a fixed order) rather than by target alone. This mirrors
# the old etl.py behavior of appending GQ control rows after the household
# controls.csv rows and numbering them sequentially, while keeping ids
# reproducible across pipeline refreshes (a materialized_view is fully
# recomputed each run).
_SOURCE_PRIORITY = {"household": 0, "gq_mil": 1, "gq_col": 2, "gq_oth": 3}
_SOURCES = [
    "bronze_controls",
    "bronze_controls_gq_mil",
    "bronze_controls_gq_col",
    "bronze_controls_gq_oth",
]


@dp.materialized_view(
    comment="Control definitions (household + GQ) with a stable per-run control_id, like old etl.py's inputs.controls",
    table_properties={"delta.feature.timestampNtz": "supported"},
)
def silver_controls():
    lookup = spark.read.table("run_id_lookup")

    def _clean(table_name):
        return (
            spark.read.table(table_name)
            .drop("_rescued_data")
            .withColumn("year", F.col("year").cast("int"))
            .join(lookup, ["run_timestamp", "year"], "left")
        )

    combined = _clean(_SOURCES[0])
    for table_name in _SOURCES[1:]:
        combined = combined.unionByName(_clean(table_name))

    priority_expr = F.lit(99)
    for name, priority in _SOURCE_PRIORITY.items():
        priority_expr = F.when(F.col("synthesis_run") == name, F.lit(priority)).otherwise(priority_expr)

    window = Window.partitionBy("run_id").orderBy("source_priority", "target")
    return (
        combined.withColumn("source_priority", priority_expr)
        .withColumn("control_id", F.row_number().over(window))
        .select(
            "run_id",
            "control_id",
            "target",
            "geography",
            "seed_table",
            "importance",
            "control_field",
            "expression",
            "synthesis_run",
            "year",
        )
    )
