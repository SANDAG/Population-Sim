# Import libraries
import pandas as pd
import numpy as np
import sqlalchemy as sql
import json
import pymssql
import sys
sys.path.insert(1, 'python')
from create_mgra_base import read_sql_file, query_database, establish_db_connection

def get_gq_mil(year):
    conn, staging_table = establish_db_connection(config_path='../config.yml')
    sql_query = read_sql_file(file_path=r'../sql/region_control_gq_mil.sql')
    sql_query = sql_query.format(staging_table=staging_table, year=year)

    mgra_based_output = query_database(sql_query, conn)
    return mgra_based_output.iloc[0][0]

def get_indxwalk(row):
        if row['Industry'] in ['State and Local Government', 'Federal Civilian']:
            return 'job_1'
        elif row['Industry'] in ['Federal Military']:
            return 'job_2'
        elif row['Industry'] in ['Forestry, fishing, and hunting', 'Farm', 'Mining']:
            return 'job_3'
        elif row['Industry'] in ['Information',
                                'Professional, scientific, and technical services', 
                                 'Administrative, support, waste management, and remediation services']:
            return 'job_4'
        elif row['Industry'] in ['Finance and insurance','Real estate and rental and leasing',
                                 'Management of companies and enterprises']:
            return 'job_5'        
        elif row['Industry'] in ['Educational services; private']:
            return 'job_6'
        elif row['Industry'] in ['Health care and social assistance']:
            return 'job_7'
        elif row['Industry'] in ['Retail trade']:
            return 'job_8'
        elif row['Industry'] in ['Construction','Transportation and warehousing' ]:
            return 'job_9'
        elif row['Industry'] in ['Utilities','Manufacturing', 'Wholesale trade']:
            return 'job_10'
        elif row['Industry'] in ['Arts, entertainment, and recreation']:
            return 'job_11'
        elif row['Industry'] in ['Accommodation']:
            return 'job_12'
        elif row['Industry'] in ['Food Service']:
            return 'job_13'
        elif row['Industry'] in ['Other services (except public administration)']:
            return 'job_14'
        
def build_forecast_production(year):
    # Download the data
    forecast_production = pd.read_excel(r'../data/Summary Forecast Production.xlsx')

    # Extract 2022 Figures 
    forecast_production['job_cat'] = forecast_production.apply(get_indxwalk, axis = 1)
    forecast_production = forecast_production.groupby(['job_cat']).agg({year: 'sum'})

    # Remove GQ Military from Job 2: 
    gq_mil = get_gq_mil(year)/1000
    forecast_production.loc['job_2', year] -= gq_mil

    # Clean Output 
    forecast_production = forecast_production*1000
    forecast_production = forecast_production.round()
    forecast_production[year] = forecast_production[year].astype(int)
    forecast_production = forecast_production.T[['job_1', 'job_2', 'job_3', 'job_4', 'job_5', 'job_6', 'job_7','job_8', 'job_9', 'job_10', 'job_11', 'job_12', 'job_13', 'job_14']]
    forecast_production.insert(0, 'region', [1])
    forecast_production.columns.name = ''
    forecast_production = forecast_production.reset_index(drop=True)

    return forecast_production

def build_labor_force_components(year):
    lf_comp = pd.read_excel(r'../data/Labor Force Components.xlsx')
    lf_comp = lf_comp[lf_comp['Race'] != 'All Races']

    # Change the Race Names
    new_race_names = {
        'White-NonHispanic': 'lfp_white',
        'Black-NonHispanic': 'lfp_black',
        'Other-NonHispanic': 'lfp_other',
        'Hispanic': 'lfp_hispanic'
    }

    # Apply the renaming
    lf_comp['Race'] = lf_comp['Race'].map(new_race_names)

    # Clean the output 
    lf_comp = lf_comp.drop(['Category', 'Units'], axis=1)
    lf_comp = lf_comp.set_index('Race').T
    lf_comp = lf_comp[['lfp_black', 'lfp_hispanic', 'lfp_other', 'lfp_hispanic']]
    lf_comp.columns.name = ''
    lf_comp = lf_comp*1000

    return lf_comp.loc[[year]].reset_index(drop=True)

def build_region_control(year):
    forecast_production = build_forecast_production(year)
    labor_force_components = build_labor_force_components(year)
    region_control = pd.concat([forecast_production, labor_force_components], axis=1)

    # Output
    region_control.to_csv(f'../2. Implementation/data/region_controls.csv', index=False)

    return region_control

# # Do Work
# for year in [2022, 2026, 2029, 2032, 2040, 2050]:
#     build_region_control(year)
#     print(f'{year} region controls have been built and loaded to PopSim.')