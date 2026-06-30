"""Entry point."""

import logging
import os
import subprocess
import sys

import yaml

# User-defined modules
from python.build_controls import get_mgra_controls, get_region_controls
from python.build_seed_data import get_seed_households, get_seed_persons
from python.outputs import create_abm_outputs, organize_outputs
from python.etl import run_etl
from python.db import get_engine

def load_configs() -> tuple[dict, dict]:
    with open("config.yml", "r") as file:
        config = yaml.safe_load(file)
    with open("secrets.yml", "r") as file:
        secrets = yaml.safe_load(file)
    return config, secrets

def write_seed_files(engine, config: dict) -> None:
    folder = "populationsim/data/"
    seed_households = get_seed_households(engine, config["sql"]["seed_households"])
    seed_persons = get_seed_persons(engine, config["sql"]["seed_persons"])
    for k in ["gq", "hh"]:
        seed_households[k].to_csv(folder + "seed_households_" + k + ".csv", index=False)
        seed_persons[k].to_csv(folder + "seed_persons_" + k + ".csv", index=False)

def write_control_files(engine, config: dict, secrets: dict, year: int) -> None:
    folder = "populationsim/data/"
    get_mgra_controls(
        sql_engine=engine,
        query_file=config["sql"]["mgra_controls"],
        schema=secrets["sql"]["schema"],
        year=year,
    ).to_csv(folder + "mgra_controls.csv", index=False)
    get_region_controls(
        sql_engine=engine,
        query_file=config["sql"]["region_controls"],
        schema=secrets["sql"]["schema"],
        econ_file=config["economic_controls"],
        year=year,
    ).to_csv(folder + "region_controls.csv", index=False)

def run_simulation() -> None:
    try:
        os.chdir("populationsim")  # Change to populationsim directory
        # Run populationsim
        subprocess.call(
            "python run_populationsim.py -c ./configs -m 22", shell=True
        )
        os.chdir("..")  # Change back to root directory
        logging.info("Simulation run successful")
    except Exception as e:
        logging.error(f"Error running simulation: {e}")

def process_year(year: int, engine, config: dict, secrets: dict) -> None:
    folder = "populationsim/data/"

    print(f"Building controls for {year}")
    write_control_files(engine, config, secrets, year)

    print(f"Running populationsim for {year}")
    run_simulation()

    organize_outputs(year=year)

    create_abm_outputs(
        year=year,
        sql_engine=engine,
        query_file=config["sql"]["mgrabase"],
        schema=secrets["sql"]["schema"],
    )

    if config["sql"]["load_to_database"]:
        run_id = run_etl(
            year=year,
            engine=engine,
            output_database=secrets["sql"]["output_database"],
            version=config["version"],
            staging_schema=secrets["sql"]["schema"],
            seed_data=config["seed_data"],
            comments=config["comments"],
        )

def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    config, secrets = load_configs()

    dbname = secrets["sql"]["output_database"] if config["sql"]["load_to_database"] else "master"
    engine = get_engine(database=dbname)

    write_seed_files(engine, config)

    for year in config["years"]:
        process_year(year, engine, config, secrets)

    logging.info("All years processed successfully.")


if __name__ == "__main__":
    sys.exit(main())
