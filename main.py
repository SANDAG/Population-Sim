"""Entry point."""

import logging
import os
import subprocess
import sys
from pathlib import Path

import yaml

# User-defined modules
from python.build_controls import get_mgra_controls, get_region_controls
from python.build_seed_data import get_seed_households, get_seed_persons
from python.outputs import create_abm_outputs, organize_outputs
from python.etl import run_etl
from python.db import get_engine

# Paths — anchored to this file so the pipeline can be run from any directory
ROOT_DIR    = Path(__file__).parent
POPSIM_DIR  = ROOT_DIR / "populationsim"
DATA_DIR    = POPSIM_DIR / "data"
CONFIGS_DIR = POPSIM_DIR / "configs"
CONFIGS_MP_DIR = POPSIM_DIR / "configs_mp"
OUTPUT_DIR  = POPSIM_DIR / "output"

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

def run_simulation(num_processes: int) -> None:
    cmd = [
        sys.executable,
        str(POPSIM_DIR / "run_populationsim.py"),
        "-c", str(CONFIGS_MP_DIR),
        "-c", str(CONFIGS_DIR),
        "-d", str(DATA_DIR),
        "-o", str(OUTPUT_DIR),
    ]
    if num_processes > 1:
        cmd += ["-m", str(num_processes)]
 
    logging.info("Running: %s", " ".join(cmd))
    # check=True raises CalledProcessError on non-zero exit, stopping the year
    # loop immediately rather than continuing on missing or corrupt output data
    subprocess.run(cmd, check=True, cwd=POPSIM_DIR)
    logging.info("Simulation run successful")

def process_year(year: int, engine, config: dict, secrets: dict) -> None:
    folder = "populationsim/data/"

    print(f"Building controls for {year}")
    write_control_files(engine, config, secrets, year)

    print(f"Running populationsim for {year}")
    run_simulation(num_processes=config.get("num_processes", 1))

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
