from pyspark import pipelines as dp
from pyspark.sql import functions as F
from pyspark.sql.window import Window


# Streaming queries can't sort, so ids are numbered here rather than with an
# identity column on the stream. Ordering by ingestion batch first keeps ids
# stable: runs already numbered keep their ids, and a run arriving in a later
# batch goes after them even if its run_timestamp is older. Within one batch
# (e.g. the initial load on a fresh build) runs are numbered oldest-first.
@dp.materialized_view(
    comment="One row per PopSim run: run_id numbered by ingestion batch, then run_timestamp",
    table_properties={"delta.feature.timestampNtz": "supported"},
)
def run_id_lookup():
    order = Window.orderBy("ingested_at", "run_timestamp", "year")
    return (
        spark.read.table("run_ingest_log")
        .withColumn("run_id", F.row_number().over(order).cast("bigint"))
        .select("run_id", "year", "run_timestamp")
    )
