"""Entry point."""

import logging
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml

# User-defined modules
from python.build_controls import get_mgra_controls, get_region_controls
from python.build_seed_data import get_seed_households, get_seed_persons
from python.outputs import create_abm_outputs, organize_outputs
from python.datalake_exporter import find_controls_paths, write_to_datalake
from python.db import get_engine

# Paths — anchored to this file so the pipeline can be run from any directory
ROOT_DIR    = Path(__file__).parent
POPSIM_DIR  = ROOT_DIR / "populationsim"
DATA_DIR    = POPSIM_DIR / "data"
CONFIGS_DIR = POPSIM_DIR / "configs"
CONFIGS_MP_DIR = POPSIM_DIR / "configs_mp"
CONFIGS_COMMON_DIR = POPSIM_DIR / "configs_common"
OUTPUT_DIR  = POPSIM_DIR / "output"
FINAL_OUTPUT_DIR = ROOT_DIR / "output"   # post-processed, year-stamped output

# Registry of GQ types — one entry per type, used to split both the seed
# extract (write_seed_files) and the control file (write_gq_control_files).
# Single source of truth so seed and control splits can't drift out of sync
# if a type is ever added, renamed, or a key gets typo'd in only one place.
GQ_TYPES = {
    "gq_mil": {"seed_type_code": 1, "control_column": "gq_mil_pop", "control_name": "GQ_Military"},
    "gq_col": {"seed_type_code": 2, "control_column": "gq_college_pop", "control_name": "GQ_College"},
    "gq_oth": {"seed_type_code": 3, "control_column": "gq_other_pop", "control_name": "GQ_Other"},
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

    for name, spec in GQ_TYPES.items():
        hh_subset = gq_households[gq_households["gq_type"] == spec["seed_type_code"]]
        persons_subset = gq_persons[gq_persons["hhid"].isin(hh_subset["hhid"])]

        if hh_subset.empty:
            logging.warning("No seed households found for %s (gq_type=%s)", name, spec["seed_type_code"])

        hh_subset.to_csv(DATA_DIR / f"seed_households_{name}.csv", index=False)
        persons_subset.to_csv(DATA_DIR / f"seed_persons_{name}.csv", index=False)

def write_gq_control_files(mgra_controls: pd.DataFrame) -> None:
    for name, spec in GQ_TYPES.items():
        pop_col = spec["control_column"]
        control_name = spec["control_name"]

        subset = mgra_controls.loc[mgra_controls[pop_col] > 0, ["mgra", pop_col]].copy()
        subset = subset.rename(columns={pop_col: control_name})

        # Total_GQ is the "total" control PopulationSim's total_hh_control setting
        # expects — structurally required alongside the type-specific target,
        # even though for a single-type run the two are numerically identical
        # (there's only one category of record in this run's seed).
        subset["Total_GQ"] = subset[control_name]

        subset = subset[["mgra", "Total_GQ", control_name]]
        subset.to_csv(DATA_DIR / f"mgra_controls_{name}.csv", index=False)

        if subset.empty:
            logging.warning("No MGRAs with %s > 0 — %s control file is empty", pop_col, name)

def write_control_files(engine, config: dict, secrets: dict, year: int) -> None:
    mgra_controls = get_mgra_controls(
        sql_engine=engine,
        query_file=config["sql"]["mgra_controls"],
        schema=secrets["sql"]["schema"],
        year=year,
    )
    mgra_controls.to_csv(DATA_DIR / "mgra_controls.csv", index=False)
    write_gq_control_files(mgra_controls)

    get_region_controls(
        sql_engine=engine,
        query_file=config["sql"]["region_controls"],
        schema=secrets["sql"]["schema"],
        econ_file=config["economic_controls"],
        year=year,
    ).to_csv(DATA_DIR / "region_controls.csv", index=False)

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

    organize_outputs(
        year=year,
        config=config,
        popsim_dir=POPSIM_DIR,
        data_dir=DATA_DIR,
        final_output_dir=FINAL_OUTPUT_DIR,
    )

    create_abm_outputs(
        year=year,
        sql_engine=engine,
        query_file=config["sql"]["mgrabase"],
        schema=secrets["sql"]["schema"],
        final_output_dir=FINAL_OUTPUT_DIR,
    )

    if config["sql"]["load_to_database"]:
        write_to_datalake(
            output_path=f"output/{year}",
            env=config["datalake"]["env"],
            metadata={
                "year": year,
                "version": config["version"],
                "seed_data": config["seed_data"],
                "comments": config["comments"],
            },
            controls_paths=find_controls_paths(config["synthesis_runs"], POPSIM_DIR),
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
