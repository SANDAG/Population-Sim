import logging
import os
from pathlib import Path
import pandas as pd
import re
import shutil
import sqlalchemy as sql


def create_abm_outputs(
    year: int, sql_engine: sql.engine, query_file: str, schema: str, final_output_dir: Path
) -> None:
    """Generate the mgrabase ABM output. Synthetic household/person merging
    now happens in organize_outputs(), which must run before this."""
    # Ensure input schema is contained by brackets
    if re.fullmatch(r"^\[.+\]", schema) is None:
        schema = "[" + schema + "]"

    year_output_dir = final_output_dir / str(year)

    # Get and write mgrabase file
    with sql_engine.connect() as connection:
        with open(query_file, "r") as query:
            mgrabase = pd.read_sql_query(
                sql.text(query.read().format(staging_schema=schema, year=year)),
                connection,
            )
    mgrabase.to_csv(year_output_dir / f"mgra15_based_input_{year}.csv", index=False)

    logging.info(f"ABM outputs created for {year}")

def _synthetic_filenames(run_name: str) -> tuple[str, str]:
    """PopulationSim writes unsuffixed filenames for the household run, but
    all GQ runs (regardless of type) write with a _gq suffix — the three GQ
    types stay distinct by output directory, not by filename."""
    if run_name == "household":
        return "synthetic_households.csv", "synthetic_persons.csv"
    return "synthetic_households_gq.csv", "synthetic_persons_gq.csv"

def merge_synthetic_population(config: dict, popsim_dir: Path, year_output_dir: Path) -> None:
    household_frames = []
    person_frames = []
    id_offset = 0

    for run in config["synthesis_runs"]:
        run_output_dir = popsim_dir / run["output"]
        hh_file, persons_file = _synthetic_filenames(run["name"])

        hh = pd.read_csv(run_output_dir / hh_file)
        persons = pd.read_csv(run_output_dir / persons_file)

        hh["household_id"] += id_offset
        persons["household_id"] += id_offset

        household_frames.append(hh)
        person_frames.append(persons)

        id_offset += len(hh)

    (
        pd.concat(household_frames, ignore_index=True)
        .drop(columns="PUMA")
        .assign(
            HHADJINC=lambda x: x["HHADJINC"].clip(0, None),
            HHT=lambda x: x["HHT"].fillna(0),
            HUPAC=lambda x: x["HUPAC"].fillna(0),
            BLD=lambda x: x["BLD"].fillna(0),
        )
    ).to_csv(year_output_dir / "synthetic_households.csv", index=False)

    (
        pd.concat(person_frames, ignore_index=True)
        .drop(columns="PUMA")
        .assign(
            ESR=lambda x: x["ESR"].fillna(0),
            COW=lambda x: x["COW"].fillna(0),
            WKHP=lambda x: x["WKHP"].fillna(0),
            SCHG=lambda x: x["SCHG"].fillna(0),
            MIL=lambda x: x["MIL"].fillna(0),
            SCHL=lambda x: x["SCHL"].fillna(0),
            OCCP=lambda x: x["OCCP"].fillna(0),
            WKW=lambda x: x["WKW"].fillna(0),
        )
    ).to_csv(year_output_dir / "synthetic_persons.csv", index=False)

def organize_outputs(year: int, config: dict, popsim_dir: Path, data_dir: Path, final_output_dir: Path) -> None:
    """Organize populationsim outputs."""

    year_output_dir = final_output_dir / str(year)
    year_output_dir.mkdir(parents=True, exist_ok=True)

    merge_synthetic_population(config, popsim_dir, year_output_dir)

    ancillary_files = [
        "timing_log.csv",
        "final_summary_mgra.csv",
        "final_summary_mgra_PUMA.csv",
        "final_summary_region_1.csv",
    ]

    for run in config["synthesis_runs"]:
        run_output_dir = popsim_dir / run["output"]
        suffix = "" if run["name"] == "household" else f"_{run['name']}"

        for filename in ancillary_files:
            src = run_output_dir / filename
            if not src.exists():
                logging.info("Skipping %s for %s — file not produced by this run", filename, run["name"])
                continue
            dst = year_output_dir / f"{src.stem}{suffix}{src.suffix}"
            shutil.copy2(src, dst)
    
    control_files = [
        "mgra_controls.csv",
        "region_controls.csv",
        "mgra_controls_gq_col.csv",
        "mgra_controls_gq_mil.csv",
        "mgra_controls_gq_oth.csv",
    ]
    for filename in control_files:
        shutil.copy2(data_dir / filename, year_output_dir / filename)

    logging.info(f"PopSim outputs organized for {year}")

