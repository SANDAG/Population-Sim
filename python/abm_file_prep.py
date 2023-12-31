import pandas as pd
import os 
import sys
import pyodbc
import yaml

sys.path.insert(1, 'python')
from create_mgra_base import read_sql_file, query_database, establish_db_connection

# Change to the top-level of the Population-Sim repository
os.chdir(os.path.dirname(os.path.realpath(__file__)))
while os.path.basename(os.getcwd()) != 'Population-Sim' and os.path.basename(os.getcwd()) != '':
    os.chdir('..')


# Combine Synthetic and GQ Populations for both households and persons 
def combine_population_data(year):
    hhgq_df = pd.read_csv(f'3. Post_processing/{year}/synthetic_households_gq.csv')
    hh_df = pd.read_csv(f'3. Post_processing/{year}/synthetic_households.csv')
    pergq_df = pd.read_csv(f'3. Post_processing/{year}/synthetic_persons_gq.csv')
    per_df = pd.read_csv(f'3. Post_processing/{year}/synthetic_persons.csv')

    hhgq_df['household_id'] += len(hh_df)
    pergq_df['household_id'] += len(hh_df)

    hhfull_df = pd.concat([hh_df, hhgq_df]).drop(columns=['PUMA'])
    hhfull_df['HHADJINC'] = hhfull_df['HHADJINC'].apply(lambda x: max(x, 0))
    hhfull_df.update(hhfull_df[['HHT', 'HUPAC', "BLD", 'GQ_type']].fillna(0))

    perfull_df = pd.concat([per_df, pergq_df]).drop(columns=['PUMA'])
    perfull_df.update(perfull_df[['ESR', 'COW', 'WKHP', 'SCHG', 'MIL', 'SCHL', 'OCCP', 'WKW']].fillna(0))

    # Save combined data or return it
    hhfull_df.to_csv(f'abm_output/{year}/synthetic_households_{year}.csv', index=False)
    perfull_df.to_csv(f'abm_output/{year}/synthetic_persons_{year}.csv', index=False)

    print(f'{year} ABM Population Sim Outputs are outputted')


# Create MGRA Based INput
def mgra_based_input_creation(year):
    conn, staging_table = establish_db_connection(config_path='config.yml')
    sql_query = read_sql_file(file_path=r'sql/mgra_base_creation.sql')
    sql_query = sql_query.format(staging_table=staging_table, year=year)

    mgra_based_output = query_database(sql_query, conn)
    mgra_based_output.to_csv(rf'abm_output/{year}/mgra15_based_input_{year}.csv', index=False)
    print(f"{year} mgra based input is outputted")

def create_abm_ouputs(year):
    # Make sure the output folder exists
    output_dir = f'abm_output/{year}'
    os.makedirs(output_dir, exist_ok=True)

    print(f'Building {year} ABM outputs')
    combine_population_data(year)
    mgra_based_input_creation(year)


# Get Data From YML File 
with open('config.yml', 'r') as file:
    config = yaml.safe_load(file)
years = config['years']

# Create Outputs for each year 
for year in years: 
    create_abm_ouputs(year)