""" This module creates seed files for use in populationsim."""

import pandas as pd
import sqlalchemy as sql


def get_seed_households(sql_engine: sql.engine, query_file: str) -> dict:
    """Get households seed files.

    Get the ACS PUMS households seed data, splitting by Group Quarters versus
    Households.

    Args:
        sql_engine (sql.engine): SQL Database connection
        query_file (str): SQL query file to return households seed data

    Returns:
        dict[pd.DataFrame, pd.DataFrame]: A two-element dictionary. The first
            element, "gq", containing the Group Quarters houesholds seed data
            and the second element, "hh", containing the Households households
            seed data.
    """
    # Get seed data
    with sql_engine.connect() as connection:
        with open(query_file, "r") as query:
            households = pd.read_sql_query(sql.text(query.read()), connection)

    # Split into Group Quarters/non-Group Quarters
    households_gq = households[households["TYPEHUGQ"].isin(["2", "3"])]
    households_hh = households[households["TYPEHUGQ"] == "1"]

    # Add the hhid field by sorting SERIALNO
    households_gq = households_gq.sort_values(by="SERIALNO")
    households_gq["hhid"] = pd.factorize(households_gq["SERIALNO"])[0] + 1
    households_hh = households_hh.sort_values(by="SERIALNO")
    households_hh["hhid"] = pd.factorize(households_hh["SERIALNO"])[0] + 1

    return {"gq": households_gq, "hh": households_hh}


def get_seed_persons(sql_engine: sql.engine, query_file: str) -> dict:
    """Get persons seed files.

    Get the ACS PUMS persons seed data, splitting by Group Quarters versus
    Households.

    Args:
        sql_engine (sql.engine): SQL Database connection
        query_file (str): SQL query file to return persons seed data

    Returns:
        dict[pd.DataFrame, pd.DataFrame]: A two-element dictionary. The first
            element, "gq", containing the Group Quarters persons seed data and
            the second element, "hh", containing the Households persons seed
            data.
    """
    # Get seed data
    with sql_engine.connect() as connection:
        with open(query_file, "r") as query:
            persons = pd.read_sql_query(sql.text(query.read()), connection)

    # Split into Group Quarters/non-Group Quarters
    persons_gq = persons[persons["TYPEHUGQ"].isin(["2", "3"])]
    persons_hh = persons[persons["TYPEHUGQ"] == "1"]

    # Add the hhid field by sorting SERIALNO
    persons_gq = persons_gq.sort_values(by=["SERIALNO", "SPORDER"])
    persons_gq["hhid"] = pd.factorize(persons_gq["SERIALNO"])[0] + 1
    persons_hh = persons_hh.sort_values(by=["SERIALNO", "SPORDER"])
    persons_hh["hhid"] = pd.factorize(persons_hh["SERIALNO"])[0] + 1

    return {"gq": persons_gq, "hh": persons_hh}
