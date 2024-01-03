# Import Libraries
import pandas as pd
import numpy as np
import pyodbc
import warnings
warnings.filterwarnings('ignore')
from functools import reduce
import yaml
import os


# The Run Code in VS Code starts at the root
try:
    os.chdir(r'python')
except Exception as e:
    print(f"Could not change directory: {e}")

# Function to read SQL file
def read_sql_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

# Function to query database
def query_database(query, conn):
    return pd.read_sql_query(query, conn)

# Function to load demographic data
def load_demographic_data(sql_file_path, staging_table, year, conn):
    sql_query = read_sql_file(sql_file_path)
    sql_query = sql_query.format(staging_table=staging_table, year=year)
    return query_database(sql_query, conn)


def establish_db_connection(config_path='../config.yml'):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    db_config = config['database']
    conn = pyodbc.connect(f"Driver={db_config['driver']};"
                          f"Server={db_config['server']};"
                          f"Database={db_config['database']};"
                          f"Trusted_Connection={db_config['trusted_connection']};")
    staging_table = config['staging']['table']
    return conn, staging_table


def load_all_data_for_year(staging_table, year, conn):
    data = {
        'sex': load_demographic_data('../sql/mgra_control_sex.sql', staging_table, year, conn),
        'age': load_demographic_data('../sql/mgra_control_age.sql', staging_table, year, conn),
        'race': load_demographic_data('../sql/mgra_control_ethnicity.sql', staging_table, year, conn),
        'household': load_demographic_data('../sql/mgra_control_hh_char.sql', staging_table, year, conn),
        'income': load_demographic_data('../sql/mgra_control_income.sql', staging_table, year, conn)
    }
    return data


def manipulate_sex_data(df):
    df_pivot = df.pivot(index='mgra', columns='sex', values='pop').reset_index()
    df_pivot.columns.name = ''
    return df_pivot[['mgra', 'Male', 'Female']]

def manipulate_age_data(df):
    df_pivot = df.pivot(index='mgra', columns='age_group', values='pop').reset_index()
    df_pivot.columns.name = ''
    return df_pivot[['mgra', 'Age_LT5', 'Age_5to9', 'Age_10to14', 'Age_15to17', 'Age_18to24', 'Age_25to34','Age_35to44', 'Age_45to54', 'Age_55to64', 'Age_65to74','Age_75to84', 'Age_85Plus']]

def manipulate_race_data(df):
    df_pivot = df.pivot(index='mgra', columns='long_name', values='hhp').reset_index()
    df_pivot.columns.name = ''
    df_pivot['Non-Hispanic, Other'] = df_pivot['Non-Hispanic, Other'] + df_pivot['Non-Hispanic, American Indian or Alaska Native'] + df_pivot['Non-Hispanic, Hawaiian or Pacific Islander']
    df_pivot = df_pivot.drop(['Non-Hispanic, American Indian or Alaska Native', 'Non-Hispanic, Hawaiian or Pacific Islander'], axis=1)
    df_pivot = df_pivot.rename(columns={'Non-Hispanic, Asian':'Asian',
                                        'Non-Hispanic, Black':'Black',
                                        'Non-Hispanic, Other':'Other_v2',
                                        'Non-Hispanic, Two or More Races':'TwoorMore',
                                        'Non-Hispanic, White':'White'})
    return df_pivot[['mgra', 'Asian', 'Black', 'Hispanic', 'Other_v2', 'TwoorMore', 'White']]


def manipulate_all_data(dataframes):
    dataframes['sex'] = manipulate_sex_data(dataframes['sex'])
    dataframes['age'] = manipulate_age_data(dataframes['age'])
    dataframes['race'] = manipulate_race_data(dataframes['race'])
    return dataframes


def combine_dataframes(dataframes_dict):
    # Extract the DataFrames from the dictionary and put them in a list
    dataframes_to_merge = [df for df in dataframes_dict.values()]
    
    # Use reduce to merge them all together
    combined_df = reduce(lambda left, right: pd.merge(left, right, on='mgra'), dataframes_to_merge)
    
    # Calculate additional columns if needed
    combined_df['Total_HH_GQ'] = combined_df['Total_HH'] + combined_df['gq_college_pop'] + combined_df['gq_mil_pop'] + combined_df['gq_other_pop']
    return combined_df

def build_mgra_control(year):
    conn, staging_table = establish_db_connection()
    dataframes = load_all_data_for_year(staging_table, year, conn)
    dataframes = manipulate_all_data(dataframes)
    output = combine_dataframes(dataframes)
    output.to_csv(rf'../populationsim/data/mgra_controls.csv', index=False)
    return output

# # Do Work 
# conn, staging_table = establish_db_connection()
# for year in [2022, 2026, 2029, 2032, 2035, 2040, 2050]:
#     build_mgra_control(year)
#     print(f"{year} mgra controls have been built and loaded to PopSim")





