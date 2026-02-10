import logging
import os
import pandas as pd
import re
import shutil
import sqlalchemy as sql


def create_abm_outputs(
    year: int, sql_engine: sql.engine, query_file: str, schema: str
) -> None:
    """Generate ABM outputs.

    Args:
        sql_engine (sql.engine): SQL Database connection
        query_file (str): SQL query file to return mgrabase data
        schema (str): Database schema containing mgrabase
        year (int): Increment year of mgrabase

    Returns:
        None
    """
    # Ensure input schema is contained by brackets
    if re.fullmatch(r"^\[.+\]", schema) is None:
        schema = "[" + schema + "]"

    try:
        folder = f"output/{year}/"

        # Combine household files and write to output directory
        households_hh = pd.read_csv(folder + "synthetic_households.csv")
        households_gq = pd.read_csv(folder + "synthetic_households_gq.csv")
        households_gq["household_id"] += len(households_hh)

        (
            pd.concat([households_hh, households_gq], ignore_index=True)
            .drop(columns="PUMA")
            .assign(
                HHADJINC=lambda x: x["HHADJINC"].clip(0, None),
                HHT=lambda x: x["HHT"].fillna(0),
                HUPAC=lambda x: x["HUPAC"].fillna(0),
                BLD=lambda x: x["BLD"].fillna(0),
            )
        ).to_csv(folder + f"synthetic_households_{year}.csv", index=False)

        # Combine person files and write to output directory
        persons_hh = pd.read_csv(folder + "synthetic_persons.csv")
        persons_gq = pd.read_csv(folder + "synthetic_persons_gq.csv")
        persons_gq["household_id"] += len(households_hh)

        (
            pd.concat([persons_hh, persons_gq], ignore_index=True)
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
        ).to_csv(folder + f"synthetic_persons_{year}.csv", index=False)

        # Get and write mgrabase file
        with sql_engine.connect() as connection:
            with open(query_file, "r") as query:
                mgrabase = pd.read_sql_query(
                    sql.text(query.read().format(staging_schema=schema, year=year)),
                    connection,
                )
        mgrabase.to_csv(folder + f"mgra15_based_input_{year}.csv", index=False)

        logging.info(f"ABM outputs created for {year}")

    except Exception as e:
        logging.error(f"Error creating ABM outputs for {year}: {e}")


def organize_outputs(year: int) -> None:
    """Organize populationsim outputs."""
    try:
        # Create new path for the standard population output
        post_process_path = f"output/{year}/"
        if not os.path.exists(post_process_path):
            os.makedirs(post_process_path)

        # Move populationsim output files
        files = {
            "gq": {
                "default_path": "populationsim/output_gq/",
                "new_path": post_process_path,
                "files": [
                    "synthetic_households_gq.csv",
                    "synthetic_persons_gq.csv",
                    "final_summary_mgra_gq.csv",
                ],
            },
            "hh": {
                "default_path": "populationsim/output/",
                "new_path": post_process_path,
                "files": [
                    "synthetic_households.csv",
                    "synthetic_persons.csv",
                    "timing_log.csv",
                ],
            },
            "controls": {
                "default_path": "populationsim/data/",
                "new_path": post_process_path,
                "files": [
                    "mgra_controls.csv",
                    "region_controls.csv",
                ],
            },
            "other_outputs": {
                "default_path": "populationsim/output/",
                "new_path": post_process_path,
                "files": [
                    "summary_mgra.csv",
                    "summary_mgra_PUMA.csv",
                    "summary_region_1.csv",
                ],
            },
        }

        for k, v in files.items():
            for file in v["files"]:
                shutil.move(v["default_path"] + file, v["new_path"] + file)

        logging.info(f"PopSim outputs organized for {year}")

    except Exception as e:
        logging.error(f"Error organizing outputs for {year}: {e}")
