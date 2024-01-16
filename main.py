"""Entry point."""

import logging
import os
import subprocess
import sqlalchemy as sql
import yaml

# User-defined modules
from python.build_controls import get_mgra_controls, get_region_controls
from python.build_seed_data import get_seed_households, get_seed_persons
from python.outputs import create_abm_outputs, organize_outputs


# Method used to run populationsim from entry point
def run_simulation():
    try:
        os.chdir("populationsim")  # Change to populationsim directory
        # Run populationsim
        subprocess.call(
            "python run_populationsim.py -c configs_mp -c configs", shell=True
        )
        os.chdir("..")  # Change back to root directory
        logging.info("Simulation run successful")
    except Exception as e:
        logging.error(f"Error running simulation: {e}")


# Set up basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Get configurations and initialize SQL engine
with open("config.yml", "r") as file:
    config = yaml.safe_load(file)
engine = sql.create_engine("mssql+pymssql://" + config["sql"]["server"] + "/")
folder = "populationsim/data/"

# Create seed files and write for use in populationsim
seed_households = get_seed_households(engine, config["sql"]["seed_households"])
seed_persons = get_seed_persons(engine, config["sql"]["seed_persons"])
for k in ["gq", "hh"]:
    seed_households[k].to_csv(folder + "seed_households_" + k + ".csv", index=False)
    seed_persons[k].to_csv(folder + "seed_persons_" + k + ".csv", index=False)

# For each year of populationsim
for year in config["years"]:
    print(f"Building controls for {year}")

    # Build and write mgra-level controls for use in populationsim
    get_mgra_controls(
        sql_engine=engine,
        query_file=config["sql"]["mgra_controls"],
        schema=config["sql"]["schema"],
        year=year,
    ).to_csv(folder + "mgra_controls.csv", index=False)

    # Build and write region-level controls for use in populationsim
    get_region_controls(
        sql_engine=engine,
        query_file=config["sql"]["region_controls"],
        schema=config["sql"]["schema"],
        econ_file=config["economic_controls"],
        year=year,
    ).to_csv(folder + "region_controls.csv", index=False)

    # Run populationsim
    print(f"Running populationsim for {year}")
    run_simulation()

    # Organize outputs of populationsim
    organize_outputs(year=year)

    # Create ABM-style outputs from populationsim
    create_abm_outputs(
        year=year,
        sql_engine=engine,
        query_file=config["sql"]["mgrabase"],
        schema=config["sql"]["schema"],
    )

logging.info("All years processed successfully.")
