from pyspark import pipelines as dp

source_root = spark.conf.get("popsim.source_root")

# One controls.csv per synthesis run (household + each GQ type); GQ runs land
# under "controls_<run>" (see datalake_exporter.export_controls_csv) so they
# stay distinct from the household control definitions.
# These are the PopSim control *definitions* (targets, expressions, importance
# weights) maintained in this repo's populationsim/configs*/controls.csv, not
# E&F inputs. The E&F control totals come from sql/mgra_controls.sql and
# sql/region_controls.sql and appear as *_control columns in final_summary_*.
_SOURCES = {
    "bronze_controls": ("controls", "household", "configs"),
    "bronze_controls_gq_mil": ("controls_gq_mil", "military GQ", "configs_gq_mil"),
    "bronze_controls_gq_col": ("controls_gq_col", "college GQ", "configs_gq_col"),
    "bronze_controls_gq_oth": ("controls_gq_oth", "other GQ", "configs_gq_oth"),
}


def _register(table_name, folder, label, config_dir):
    @dp.table(
        name=table_name,
        comment=(
            f"Raw {label} control definitions (targets, expressions, importance weights) "
            f"from populationsim/{config_dir}/controls.csv in the Population-Sim repo, "
            "not E&F control totals"
        ),
        table_properties={"delta.feature.timestampNtz": "supported"},
    )
    def _bronze():
        return (
            spark.readStream.format("cloudFiles")
            .option("cloudFiles.format", "parquet")
            .load(f"{source_root}/{folder}/")
        )


for _table_name, (_folder, _label, _config_dir) in _SOURCES.items():
    _register(_table_name, _folder, _label, _config_dir)
