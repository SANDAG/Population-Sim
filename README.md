# SANDAG PopulationSim Repository

## Introduction

This repository is dedicated to running PopulationSim, a powerful demographic simulation tool used by SANDAG to translate marginal control totals produced by the Estimates & Forecast team to micro-simulated households and persons for use by SANDAG's Activity-Based Model team.

PopulationSim is well-suited for generating detailed household and person-level synthetic populations based on sample data and control totals. It is a important component in urban planning and transportation modeling. Learn more about PopulationSim in its [official documentation](https://activitysim.github.io/populationsim/).

## Getting Started

### Running PopulationSim

1. **Clone the Repository** and ensure an installation of [uv](https://docs.astral.sh/uv/) exists. Use the `pyproject.toml` file in the root directory of the project to create the Python virtual environment needed to run the project with `uv sync`.

2. **Configuration of Private Data in secrets.yml**
In order to avoid exposing certain data to the public this repository uses a secrets file to store sensitive configurations in addition to a standard configuration file. This file is stored in the root directory of the repository as `secrets.yml` and is included in the `.gitignore` intentionally to avoid it ever being committed to the repository.

The `secrets.yml` should mirror the following structure. 
```yaml
sql:
  server: "<SQLInstanceName>" # SQL instance containing seed and control data
  schema: "<[SQLSchemaName]>" # E&F team Series 15 UDM schema to use for control data
  output_database: "<SQLoutputDatabaseName>" # Optional; only used by the Streamlit report app (report/report.py), not by the PopulationSim run
```
3. **Update the `config.yml` configuration file** in the project root directory

```yaml
sql:
  seed_households: "sql/seed_households.sql" # household seed data query
  seed_persons: "sql/seed_persons.sql" # person seed data query
  mgra_controls: "sql/mgra_controls.sql" # mgra controls data query
  region_controls: "sql/region_controls.sql" # region controls data query
  mgrabase: "sql/mgrabase.sql" # mgrabase file generation data query
  load_to_database: True # Write outputs to the Azure datalake (for ingestion by the Databricks pipeline); set to False to skip the export

datalake:
  env: dev # Required when exporting; use 'dev' or 'prod'

economic_controls: "data/Economic Team Region Controls.csv" # region economic controls provided by SANDAG's Economics Team

years: # years for which to generate controls and run populationsim
  - 2022
  - 2026
  - 2029
  - 2032
  - 2035
  - 2040
  - 2050
```

4. **Update PopulationSim configuration files** (if necessary)

   - SANDAG commonly sets the `populationsim/conigs_mp/settings.yaml` file such that `multiprocess: True`, `num_processes: 22`, `multiprocess_steps: num_processes: 22` to enable the maximum level of multiprocessing using the 22 San Diego PUMAS as the `slice_geography: PUMA`. If at least 22 logical processors are not available (not advised due to long run times), it is suggested to set both `num_processes:` configurations to the number of logical processors.
   - See the PopulationSim [official documentation](https://activitysim.github.io/populationsim/)

5. **Run the `main.py` entry point file** from the project root directory:
  **On Windows:**
  ```bash
  uv run main.py
  ```
## Outputs of PopulationSim

Once completed, the output folder will contain subfolders for each year specified in the `config.yml` file. Each subfolder will contain the following files.

| File                            | Description                                                                 |
| ------------------------------- | --------------------------------------------------------------------------- |
| synthetic_persons_gq.csv        | PopulationSim output synthetic group quarters persons                       |
| synthetic_persons.csv           | PopulationSim output synthetic persons (non-group quarters)                 |
| synthetic*persons*`year`.csv    | Combined synthetic persons file for use by the Activity-Based Model team    |
| synthetic_households_gq.csv     | PopulationSim output synthetic group quarters households                    |
| synthetic_households.csv        | PopulationSim output synthetic households (non-group quarters)              |
| synthetic*households*`year`.csv | Combined synthetic households file for use by the Activity-Based Model team |
| mgra15*based_input*`year`.csv   | The mgrabase file for use by the Activity-Based Model team                  |
| timing_log.csv                  | PopulationSim log of process runtimes                                       |


If running PopulationSim as an _official run_ for use by SANDAG's QA and/or Activity-Based Model teams, update the version tracker at: `\\sandag.org\transdata\socioec\Current_Projects\SR15\version_history.xlsx`

*Note: This is temporary until ABM team feels comfortable with use of production SQL database*

### Databricks Lakehouse Pipeline
This repository contains the option in `config.yml` (`load_to_database: True`) to export PopulationSim outputs to an Azure Data Lake as Parquet via `python/datalake_exporter.py`. A Databricks Lakeflow Declarative Pipeline (`databricks/`) then ingests and transforms those files into Delta tables across three layers:

- **Bronze** (`databricks/transformations/bronze/`):  raw Auto Loader ingestion of every PopSim export: synthetic households/persons, run metadata, MGRA/PUMA/region final summaries (household + each GQ type), control definitions, seed households/persons, and the `mgra15_based_input` ABM file.
- **Silver** (`databricks/transformations/silver/`): cleaned, typed tables with a stable `run_id` attached via `run_id_lookup`/`run_info`, plus `silver_control_definitions` and `silver_control_totals`, which reproduce a unified control-vs-result comparison across every geography and synthesis run.
- **Gold** (`databricks/transformations/gold/`): BI-ready aggregate marts such as `gold_household_demographics` and `gold_population_by_mgra`.

A Databricks job (`databricks/resources/populationsim.job.yml`) with a file arrival trigger starts a pipeline update once `datalake_exporter.py` finishes writing a run's export, signaled by a `_export_status/<year>/_SUCCESS_*.json` completion marker. See `databricks.yml` and `databricks/resources/populationsim.pipeline.yml` for the bundle configuration.

#### Pausing or enabling the file arrival trigger
Whether the trigger fires is controlled by `trigger.pause_status` in `databricks/resources/populationsim.job.yml`:

- `UNPAUSED`: each completed export starts a pipeline update automatically.
- `PAUSED`: exports land in the volume but nothing runs until running the pipeline in the Databricks UI


### Streamlit Report App
This repository contains a Streamlit app that generates validation reports for PopulationSim outputs stored in SANDAG's production database. You can use it to visualize the results of the run interactively using Streamlit's easy-to-use interface. The documentation can be found here https://docs.streamlit.io/.

#### Prerequisites
Before generating the report, ensure that you have the following:
- Set the proper SQL instance and database containing PopulationSim outputs in the `secrets.yml`.
- Are running in a Python virtual environment with all required dependencies listed in the `environment.yml`.

#### Generate validation reports
Run the Streamlit app in the base project directory with the following command.
```bash
uv run -- streamlit run report/report.py
```
