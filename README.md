# SANDAG PopulationSim Repository

## Introduction

This repository is dedicated to running PopulationSim, a powerful demographic simulation tool used by SANDAG to translate marginal control totals produced by the Estimates & Forecast team to micro-simulated households and persons for use by SANDAG's Activity-Based Model team.

PopulationSim is well-suited for generating detailed household and person-level synthetic populations based on sample data and control totals. It is a important component in urban planning and transportation modeling. Learn more about PopulationSim in its [official documentation](https://activitysim.github.io/populationsim/).

## Getting Started

### Running PopulationSim

1. **Clone the Repository** and ensure an installation of [Miniconda/Anaconda](https://docs.conda.io/projects/miniconda/en/latest/) exists. Use the `environment.yml` file in the root directory of the project to [create the Python virtual environment](https://docs.conda.io/projects/conda/en/4.6.1/user-guide/tasks/manage-environments.html#creating-an-environment-from-an-environment-yml-file) needed to run the project.

2. **Configuration of Private Data in secrets.yml**
In order to avoid exposing certain data to the public this repository uses a secrets file to store sensitive configurations in addition to a standard configuration file. This file is stored in the root directory of the repository as `secrets.yml` and is included in the `.gitignore` intentionally to avoid it ever being committed to the repository.

The `secrets.yml` should mirror the following structure. 
```yaml
sql:
  server: "<SQLInstanceName>" # SQL instance containing seed and control data
  schema: "<[SQLSchemaName]>" # E&F team Series 15 UDM schema to use for control data
  output_database: "<SQLoutputDatabaseName>" # Optional PopulationSim output SQL database
```
3. **Update the `config.yml` configuration file** in the project root directory

```yaml
sql:
  seed_households: "sql/seed_households.sql" # household seed data query
  seed_persons: "sql/seed_persons.sql" # person seed data query
  mgra_controls: "sql/mgra_controls.sql" # mgra controls data query
  region_controls: "sql/region_controls.sql" # region controls data query
  mgrabase: "sql/mgrabase.sql" # mgrabase file generation data query
  load_to_database: False # Set to True to Load results to database

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

5. **Run the `main.py` entry point file** from the project root directory

### Outputs of PopulationSim

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
| Validation Report.html          | Optional HTML validation report, only appears if data loaded to database    |

If running PopulationSim as an _official run_ for use by SANDAG's QA and/or Activity-Based Model teams, update the version tracker at: `sandag.org\\transdata\socioec\Current_Projects\SR15\version_history.xlsx`

*Note: This is temporary until ABM team feels comfortable with use of production SQL database*
