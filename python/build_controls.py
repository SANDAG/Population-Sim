""" This module creates control files for use in populationsim."""

import pandas as pd
import re
import sqlalchemy as sql


def get_mgra_controls(
    sql_engine: sql.engine, query_file: str, schema: str, year: int
) -> pd.DataFrame:
    """Get mgra-level controls.

    Args:
        sql_engine (sql.engine): SQL Database connection
        query_file (str): SQL query file to return mgra control data
        schema (str): Database schema containing controls
        year (int): Increment year of mgra controls

    Returns:
        pd.DataFrame: mgra-level controls
    """
    # Ensure input schema is contained by brackets
    if re.fullmatch(r"^\[.+\]", schema) is None:
        schema = "[" + schema + "]"

    # Get control data
    with sql_engine.connect() as connection:
        with open(query_file, "r") as query:
            controls = pd.read_sql_query(
                sql.text(query.read().format(staging_schema=schema, year=year)),
                connection,
            )

    return controls


def get_region_controls(
    sql_engine: sql.engine, query_file: str, schema: str, econ_file: str, year: int
) -> pd.DataFrame:
    """Get region-level controls.

    Args:
        sql_engine (sql.engine): SQL Database connection
        query_file (str): SQL query file to return mgra control data
        schema (str): Database schema containing controls
        econ_file (str): File path to economic control totals
        year (int): Increment year of mgra controls

    Returns:
        pd.DataFrame: region-level controls
    """
    # Ensure input schema is contained by brackets
    if re.fullmatch(r"^\[.+\]", schema) is None:
        schema = "[" + schema + "]"

    # Get SQL control data
    with sql_engine.connect() as connection:
        with open(query_file, "r") as query:
            sql_controls = pd.read_sql_query(
                sql.text(query.read().format(staging_schema=schema, year=year)),
                connection,
            )

    # Get Economic control data
    # Remove Military Group Quarters Region total from Job Type 2
    controls = (
        pd.read_csv(econ_file)
        .pivot_table(
            index="region", columns="Label", values=str(year), aggfunc="sum", dropna=True
        )
        .reset_index()
        .assign(job_2=lambda x: x["job_2"] - sql_controls["gq_mil"][0])[
            [
                "region",
                "job_1",
                "job_2",
                "job_3",
                "job_4",
                "job_5",
                "job_6",
                "job_7",
                "job_8",
                "job_9",
                "job_10",
                "job_11",
                "job_12",
                "job_13",
                "job_14",
                "lfp_black",
                "lfp_hispanic",
                "lfp_other",
                "lfp_white",
            ]
        ]
    )

    return controls
