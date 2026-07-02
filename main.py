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
CONFIGS_COMMON_DIR = POPSIM_DIR / "configs_common"
OUTPUT_DIR  = POPSIM_DIR / "output"

# GQ type codes, matching the control expressions in controls.csv
# (households.gq_type == 1 -> military, == 2 -> college, == 3 -> other)
GQ_TYPES = {
    "gq_mil": 1,
    "gq_col": 2,
    "gq_oth": 3,
}

def load_configs() -> tuple[dict, dict]:
    with open("config.yml", "r") as file:
        config = yaml.safe_load(file)
    with open("secrets.yml", "r") as file:
        secrets = yaml.safe_load(file)
    return config, secrets

def write_seed_files(engine, config: dict) -> None:
    seed_households = get_seed_households(engine, config["sql"]["seed_households"])
    seed_persons = get_seed_persons(engine, config["sql"]["seed_persons"])

    # Household seed
    seed_households["hh"].to_csv(DATA_DIR / "seed_households_hh.csv", index=False)
    seed_persons["hh"].to_csv(DATA_DIR / "seed_persons_hh.csv", index=False)

    # GQ seed — split the combined extract into one file per type, so each
    # configs_gq_*/ run only ever sees its own type's records.
    gq_households = seed_households["gq"]
    gq_persons = seed_persons["gq"]

    for name, gq_type in GQ_TYPES.items():
        hh_subset = gq_households[gq_households["gq_type"] == gq_type]
        persons_subset = gq_persons[gq_persons["hhid"].isin(hh_subset["hhid"])]

        if hh_subset.empty:
            logging.warning("No seed households found for %s (gq_type=%s)", name, gq_type)

        hh_subset.to_csv(DATA_DIR / f"seed_households_{name}.csv", index=False)
        persons_subset.to_csv(DATA_DIR / f"seed_persons_{name}.csv", index=False)

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

def run_simulation(configs_dirs: list[Path], data_dir: Path, output_dir: Path, num_processes: int = 1) -> None:
    cmd = [sys.executable, str(POPSIM_DIR / "run_populationsim.py")]
    for c in configs_dirs:
        cmd += ["-c", str(c)]
    cmd += ["-d", str(data_dir), "-o", str(output_dir)]
    if num_processes > 1:
        cmd += ["-m", str(num_processes)]

    logging.info("Running: %s", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=POPSIM_DIR)
    logging.info("Simulation run successful: %s", output_dir.name)

def process_year(year: int, engine, config: dict, secrets: dict) -> None:
    folder = "populationsim/data/"

    print(f"Building controls for {year}")
    write_control_files(engine, config, secrets, year)

    for run in config["synthesis_runs"]:
        print(f"Running populationsim: {run['name']} ({year})")
        run_simulation(
            configs_dirs=[POPSIM_DIR / c for c in run["configs"]],
            data_dir=POPSIM_DIR / run["data"],
            output_dir=POPSIM_DIR / run["output"],
            num_processes=run.get("num_processes", 1)
        )

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
