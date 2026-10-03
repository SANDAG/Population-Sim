from pyspark import pipelines as dp
from pyspark.sql import functions as F

source_root = spark.conf.get("popsim.source_root")

# final_summary_mgra_gq.csv from the old single-GQ-type add-on has been
# replaced by one file per GQ type; each is tagged with its synthesis_run
# here so silver/gold can disambiguate the "Total_GQ" target every GQ type
# shares.
_SOURCES = {
    "bronze_final_summary_mgra_gq_mil": "gq_mil",
    "bronze_final_summary_mgra_gq_col": "gq_col",
    "bronze_final_summary_mgra_gq_oth": "gq_oth",
}


def _register(table_name, synthesis_run):
    @dp.table(
        name=table_name,
        comment=f"Raw MGRA-level final summary for the {synthesis_run} GQ run",
        table_properties={"delta.feature.timestampNtz": "supported"},
    )
    def _bronze():
        return (
            spark.readStream.format("cloudFiles")
            .option("cloudFiles.format", "parquet")
            .load(f"{source_root}/final_summary_mgra_{synthesis_run}/")
            .withColumn("synthesis_run", F.lit(synthesis_run))
        )


for _table_name, _synthesis_run in _SOURCES.items():
    _register(_table_name, _synthesis_run)
