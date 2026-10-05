from pyspark import pipelines as dp

source_root = spark.conf.get("popsim.source_root")

# Seed households are ACS PUMS records pulled by sql/seed_households.sql and written
# by main.py to populationsim/data/ (not tracked in the repo), not the output/<year>
# folder, and are exported separately (see datalake_exporter.export_seed_csv).
_SOURCES = {
    "bronze_seed_households": ("seed_households", "household"),
    "bronze_seed_households_gq_mil": ("seed_households_gq_mil", "military GQ"),
    "bronze_seed_households_gq_col": ("seed_households_gq_col", "college GQ"),
    "bronze_seed_households_gq_oth": ("seed_households_gq_oth", "other GQ"),
}


def _register(table_name, folder, label):
    @dp.table(
        name=table_name,
        comment=f"Raw {label} seed households: ACS PUMS records extracted by sql/seed_households.sql ({folder})",
        table_properties={"delta.feature.timestampNtz": "supported"},
    )
    def _bronze():
        return (
            spark.readStream.format("cloudFiles")
            .option("cloudFiles.format", "parquet")
            .load(f"{source_root}/{folder}/")
        )


for _table_name, (_folder, _label) in _SOURCES.items():
    _register(_table_name, _folder, _label)
