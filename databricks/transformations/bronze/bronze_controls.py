from pyspark import pipelines as dp

source_root = spark.conf.get("popsim.source_root")

# One controls.csv per synthesis run (household + each GQ type); GQ runs land
# under "controls_<run>" (see datalake_exporter.export_controls_csv) so they
# stay distinct from the household control definitions.
_SOURCES = {
    "bronze_controls": "controls",
    "bronze_controls_gq_mil": "controls_gq_mil",
    "bronze_controls_gq_col": "controls_gq_col",
    "bronze_controls_gq_oth": "controls_gq_oth",
}


def _register(table_name, folder):
    @dp.table(
        name=table_name,
        comment=f"Raw control definitions ingested from PopSim configs ({folder})",
        table_properties={"delta.feature.timestampNtz": "supported"},
    )
    def _bronze():
        return (
            spark.readStream.format("cloudFiles")
            .option("cloudFiles.format", "parquet")
            .load(f"{source_root}/{folder}/")
        )


for _table_name, _folder in _SOURCES.items():
    _register(_table_name, _folder)
