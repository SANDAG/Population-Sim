from pyspark import pipelines as dp

source_root = spark.conf.get("popsim.source_root")

# Seed persons live under populationsim/data/, not the output/<year>
# folder, and are exported separately (see datalake_exporter.export_seed_csv).
_SOURCES = {
    "bronze_seed_persons": "seed_persons",
    "bronze_seed_persons_gq_mil": "seed_persons_gq_mil",
    "bronze_seed_persons_gq_col": "seed_persons_gq_col",
    "bronze_seed_persons_gq_oth": "seed_persons_gq_oth",
}


def _register(table_name, folder):
    @dp.table(
        name=table_name,
        comment=f"Raw seed persons ingested from PopSim data ({folder})",
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
