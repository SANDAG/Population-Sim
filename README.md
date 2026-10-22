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

### Azure Data Lake Export
This repository contains the option in `config.yml` (`load_to_database: True`) to export PopulationSim outputs to an Azure Data Lake as Parquet via `python/datalake_exporter.py`. Once a run's export is complete, the exporter writes a `_export_status/<year>/_SUCCESS_*.json` completion marker.

The Databricks pipeline that ingests and transforms these exports (bronze/silver/gold layers, file arrival trigger, and bundle configuration) is maintained in the `databricks-projects` repository under `src/python/jobs/transformation/population_sim`.


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

#### Reporting-only controls
For the report's **Local Output** source, `lfp_black`, `lfp_hispanic`,
`lfp_other`, and `lfp_white` are reporting benchmarks rather than fitting
constraints. Their definitions live in `populationsim/configs/reporting_controls.csv`;
they are not passed to PopulationSim through `controls.csv`.

The report compares the saved `region_controls.csv` targets against counts from
the final synthetic population, using only non-GQ persons with ESR 1, 2, or 3.
These rows appear as **Benchmark Only** in the regional table and plots. Saved
PopulationSim summary rows remain **Fitting Control** and are not recomputed.
Missing targets or population files produce unavailable values, not zero counts;
percentage differences are unavailable when the target is zero.

New runs archive active control definitions and reporting definitions alongside
their outputs. Older local outputs without snapshots fall back to the current
definitions. The database reporting path is unchanged.

The `lfp_other` definition includes `RAC1P == 9` (`Two or More Races`) along with
the other non-Hispanic race categories represented by that benchmark. Databricks
ingests `reporting_controls.csv` and the saved
`region_controls.csv` independently from the active fitting-control definitions;
the resulting `silver_control_comparisons` table marks each row's status and
leaves missing targets or model results null.
