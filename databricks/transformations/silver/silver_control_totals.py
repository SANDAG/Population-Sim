from pyspark import pipelines as dp
from pyspark.sql import functions as F

_ID_COLS = ["run_id", "geography", "id", "synthesis_run"]


def _melt_summary(df):
    """Reshape a PopSim summary file (wide, one _control/_result column pair
    per target) into long form: one row per geography/id/target. Mirrors old
    etl.py's sub_geography_summary_manipulations melt+merge."""
    control_cols = [c for c in df.columns if c.endswith("_control")]
    targets = [c[: -len("_control")] for c in control_cols]
    control_expr = "stack({0}, {1}) as (target, control_value)".format(
        len(targets), ", ".join(f"'{t}', `{t}_control`" for t in targets)
    )
    result_expr = "stack({0}, {1}) as (target, result)".format(
        len(targets), ", ".join(f"'{t}', `{t}_result`" for t in targets)
    )
    control_long = df.select(*_ID_COLS, F.expr(control_expr))
    result_long = df.select(*_ID_COLS, F.expr(result_expr))
    return control_long.join(result_long, _ID_COLS + ["target"])


@dp.materialized_view(
    comment="Unified control-vs-result totals across all geographies and synthesis runs, long format, like old etl.py's outputs.control_totals",
    table_properties={"delta.feature.timestampNtz": "supported"},
)
def silver_control_totals():
    mgra = (
        spark.read.table("silver_final_summary_mgra")
        .withColumn("synthesis_run", F.lit("household"))
        .transform(_melt_summary)
    )
    puma = (
        spark.read.table("silver_final_summary_mgra_puma")
        .withColumn("synthesis_run", F.lit("household"))
        .transform(_melt_summary)
    )
    # region_1 has one row per target already (control_name/control_value/
    # mgra_integer_weight), so it's reshaped directly rather than melted.
    region = (
        spark.read.table("silver_final_summary_region")
        .withColumn("synthesis_run", F.lit("household"))
        .select(
            "run_id",
            F.lit("region").alias("geography"),
            F.lit(1).alias("id"),
            "synthesis_run",
            F.col("control_name").alias("target"),
            "control_value",
            F.col("mgra_integer_weight").alias("result"),
        )
    )
    gq = spark.read.table("silver_final_summary_mgra_gq").transform(_melt_summary)

    summary = mgra.unionByName(puma).unionByName(region).unionByName(gq)

    controls = spark.read.table("silver_controls").select(
        "run_id", "synthesis_run", "target", "control_id"
    )

    return (
        summary.join(controls, ["run_id", "synthesis_run", "target"], "inner")
        .withColumnRenamed("id", "geography_id")
        .select("run_id", "geography", "geography_id", "control_id", "control_value", "result")
    )
