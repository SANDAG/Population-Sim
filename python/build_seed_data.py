import pandas as pd
import numpy as np
import sys

sys.path.insert(1, 'python')
from create_mgra_controls import read_sql_file, query_database, establish_db_connection

import pandas as pd

def clean_esr(esr):
    """Assigns 1 if ESR is 1, 2, or 3, otherwise 0."""
    return 1 if esr in [1, 2, 3] else 0

def build_persons_all(read_sql_file, query_database):
    # Download the data
    conn, _ = establish_db_connection(config_path='../config.yml')
    sql_query = read_sql_file(r'../sql/persons_all.sql')
    persons_all_sql = query_database(sql_query, conn)

    # SERIALNO that do not exist 
    persons_serialno_to_remove = pd.read_csv(r'../data/persons_SERIALNO_not_in_persons_all_seed_data.csv')
    persons_serialno_to_remove['SERIALNO'] = persons_serialno_to_remove['SERIALNO'].astype(str)
    persons_all = persons_all_sql[~persons_all_sql['SERIALNO'].isin(list(persons_serialno_to_remove['SERIALNO']))]
    
    # Add the HHID numerically
    persons_all['HHID'] = pd.factorize(persons_all['SERIALNO'])[0] + 1 

    # Cleaning to match the seed CSV
    persons_all['AGEP'] = persons_all['AGEP'].astype(int)
    persons_all['SCHG'].replace(to_replace=[None], value=0, inplace=True)
    persons_all['COW'] = persons_all['COW'].astype(float)
    persons_all['ESR'] = persons_all['ESR'].astype(float)
    persons_all['MIL'] = persons_all['MIL'].astype(float)
    persons_all['SPORDER'] = persons_all['SPORDER'].astype(int)
    persons_all['PUMA'] = persons_all['PUMA'].astype(int)
    persons_all['SCHG'] = persons_all['SCHG'].astype(int)
    persons_all['SEX'] = persons_all['SEX'].astype(int)

    # Build the isinlaborforce (1 for ESR 1,2,3 and 0 otherwise)
    persons_all['isinlaborforce'] = persons_all['ESR'].apply(clean_esr)

    # Arrange the final output
    persons_all = persons_all[['SERIALNO', 'HHID', 'SPORDER', 'PUMA', 'AGEP', 'SCHG', 'COW', 'SEX', 'ESR', 'MIL', 'WKHP', 'isinlaborforce']]
    
    return persons_all



def build_households_all(read_sql_file, query_database, build_persons_all):
    # Read the households SQL data
    conn, _ = establish_db_connection(config_path='../config.yml')
    sql_query = read_sql_file(r'../sql/households_all.sql')
    households_all_sql = query_database(sql_query, conn)

    # Remove SERIALNOs that do not exist in the seed data
    households_serialno_to_remove = pd.read_csv(r'../data/households_SERIALNO_not_in_households_all_seed_data.csv')
    households_serialno_to_remove['SERIALNO'] = households_serialno_to_remove['SERIALNO'].astype(str)
    households_all = households_all_sql[~households_all_sql['SERIALNO'].isin(list(households_serialno_to_remove['SERIALNO']))]

    # Merge with the HHID from persons_all
    persons_all_hhid = build_persons_all(read_sql_file, query_database)[['SERIALNO', 'HHID']].drop_duplicates()
    households_all = households_all.merge(persons_all_hhid, on='SERIALNO', how='left')

    # TODO: Match the datatypes as required

    return households_all