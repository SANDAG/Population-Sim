""" This module runs the ETL process for populationsim."""

from typing import Dict, Callable
import pandas as pd
import sqlalchemy as sql
from sqlalchemy.orm import Session
from sqlalchemy import insert
import sqlalchemy.engine.base
import yaml
import csv

def region_summary_transformations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms the region level summary file to fit within the outputs.control_totals table.
    
    Parameters:
    - df (DataFrame): The input dataframe containing 'control_name', 'control_value', and 'mgra_integer_weight'.
    
    Returns:
    - DataFrame: Transformed dataframe with 'geography', 'id', 'target', 'control', and 'result' columns.
    """
    df = df[['control_name', 'control_value', 'mgra_integer_weight']]
    df.insert(0, 'geography', 'region')
    df.insert(1, 'id', 1)
    df.columns = ['geography', 'id', 'target', 'control', 'result']
    return df

def sub_geography_summary_manipulations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms non region level summary files to fit within the outputs.control_totals table.
    
    Parameters:
    - df (DataFrame): The input dataframe with varying control and result columns.
    
    Returns:
    - DataFrame: Merged dataframe with 'geography', 'id', 'target', 'control', and 'result' columns.
    """
    # Seperate Controls and Results
    control_cols = [col for col in df.columns if col.endswith('_control')]
    result_cols = [col for col in df.columns if col.endswith('_result')]

    # Long format
    df_control = df.melt(id_vars=['geography', 'id'], value_vars=control_cols,
                        var_name='target', value_name='control')
    df_result = df.melt(id_vars=['geography', 'id'], value_vars=result_cols,
                        var_name='target', value_name='result')

    # Strip the endings 
    df_control['target'] = df_control['target'].str.replace('_control', '')
    df_result['target'] = df_result['target'].str.replace('_result', '')

    # Merge and complete 
    return pd.merge(df_control, df_result, on=['geography', 'id', 'target'])

def get_next_run_id(engine: sqlalchemy.engine.base.Engine, config: Dict) -> int:
    """
    Retrieves the next available numeric run_id from the database based on the maximum existing run_id.
    
    Parameters:
    - engine (Engine): SQLAlchemy engine instance connected to the database.
    - config (dict): Configuration dictionary containing database schema information.
    
    Returns:
    - int: The next run_id to be used.
    """
    query = sql.text(f"SELECT MAX(run_id) as max_run_id FROM {config['sql']['output_database']}.[metadata].[run]")
    with engine.connect() as connection:
        result = connection.execute(query).scalar()
        return result + 1 if result else 1

def generate_control_id_mapping(engine: sqlalchemy.engine.base.Engine, run_id: int, config: Dict) -> Dict[str, int]:
    """
    Generates a mapping of control_id to target based on a specified run_id's already outputed controls table (as controls may vary by run_id)
    
    Parameters:
    - engine (Engine): SQLAlchemy engine instance connected to the database.
    - run_id (int): The run_id to filter controls.
    - config (dict): Configuration dictionary containing database schema information.
    
    Returns:
    - dict: A dictionary mapping 'target' to 'control_id'.
    """
    query = sql.text(f"SELECT control_id, target FROM {config['sql']['output_database']}.[inputs].[controls] WHERE run_id = {run_id}")
    with engine.connect() as connection:
        result = connection.execute(query)
        rows = result.fetchall()
        control_id_mapping = {row[1]: row[0] for row in rows}
        return control_id_mapping

def add_control_id(df: pd.DataFrame, engine: sqlalchemy.engine.base.Engine, run_id: int, config: Dict, control_column: str = 'target') -> pd.DataFrame:
    """
    Adds a 'control_id' column to the dataframe based on a mapping built from the controls table for this run_id.
    
    Parameters:
    - df (DataFrame): The input dataframe to which 'control_id' will be added.
    - engine (Engine): SQLAlchemy engine instance connected to the database.
    - run_id (int): The run_id used to filter controls for mapping.
    - config (dict): Configuration dictionary containing database schema information. This comes from the generate_control_id_mapping function.
    - control_column (str): The column name in df that corresponds to 'target' in the control_id mapping.
    
    Returns:
    - DataFrame: The input dataframe with a 'control_id' column added.
    """
    # Assign control_id based on the provided mapping
    control_id_mapping = generate_control_id_mapping(engine, run_id, config)
    df['control_id'] = df[control_column].map(control_id_mapping)
    return df[df['control_id'].notnull()]

def load_to_sql(df: pd.DataFrame, name: str, con: sqlalchemy.engine.base.Engine, schema: str) -> None:
    """
    Bulk Loads a DataFrame to a SQL table, handling NULL values.
    
    Parameters:
    - df (DataFrame): The pandas DataFrame to be loaded.
    - name (str): The name of the SQL table to load the data into.
    - con (Engine): The SQLAlchemy engine connection.
    - schema (str): The schema of the target SQL table.
    """
    insert_blocks = df.to_dict('records')
    
    # Replace nan values with None (NULL) in each dictionary
    for block in insert_blocks:
        for key, value in block.items():
            if pd.isna(value):  
                block[key] = None  

    table = sql.Table(
        name,
        sql.MetaData(),
        schema=schema,
        autoload_with=con,
    )
    
    # Bulk insert
    with Session(con) as session:
        session.execute(insert(table), insert_blocks)
        session.commit()

def etl_controls_csv(run_id: int, filepath: str, engine: sqlalchemy.engine.base.Engine, table_name: str, schema: str) -> None:
    """
    Reads the controls csv, adds a 'run_id' and generates 'control_id', then loads it into a SQL table.
    
    Parameters:
    - run_id (int): The run identifier to be added to the DataFrame.
    - filepath (str): The path of the CSV file to be read.
    - engine (Engine): The SQLAlchemy engine connection.
    - table_name (str): The name of the target SQL table.
    - schema (str): The schema of the target SQL table.
    """
    df = pd.read_csv(filepath)
    df.insert(0, 'run_id', run_id)
    df['control_id'] = range(1, len(df) + 1)
    load_to_sql(df=df, name=table_name, con=engine, schema=schema)

def etl_final_summary(engine: sqlalchemy.engine.base.Engine, run_id: int, year: int, transformations_func: Callable[[pd.DataFrame], pd.DataFrame], input_path: str, output_table: str, schema: str, config: Dict) -> None:
    """
    Transforms summary data and loads it into a SQL table after applying transformations from the inputted transformation function and adding control IDs.
    
    Parameters:
    - engine (Engine): The SQLAlchemy engine connection.
    - run_id (int): The run identifier.
    - year (int): The year of the summary data.
    - transformations_func (function): The function with the necessary transformations for the given summary file
    - input_path (str): The path of the input CSV file.
    - output_table (str): The name of the target SQL table.
    - schema (str): The schema of the target SQL table.
    - config (dict): Configuration dictionary containing database schema information.
    """
    df = pd.read_csv(f'output/{year}/{input_path}')
    df = transformations_func(df)
    df.insert(0, 'run_id', run_id)
    df = add_control_id(df, engine, run_id, config, control_column='target')
    df = df.rename(columns={'id': 'geography_id', 'control':'control_value'})
    df = df[['run_id', 'geography', 'geography_id', 'control_id', 'control_value', 'result']]
    load_to_sql(df=df, name=output_table, con=engine, schema=schema)

def load_simple_files_to_sql(engine: sqlalchemy.engine.base.Engine, csv_path: str, run_id: int, schema: str, table_name: str) -> None:
    """
    Loads records from a CSV file to a SQL table with some preprocessing.
    
    Parameters:
    - engine (Engine): The SQLAlchemy engine connection.
    - csv_path (str): The path of the CSV file to be loaded.
    - run_id (int): The run identifier to be added to each record.
    - schema (str): The schema of the target SQL table.
    - table_name (str): The name of the target SQL table.
    """
    # Define the table metadata
    table = sql.Table(
        table_name,
        sql.MetaData(),
        schema=schema,
        autoload_with=engine,
    )
    
    # Read records from CSV
    insert_records = []
    with open(csv_path, "r") as csv_file:
        csv_reader = csv.reader(csv_file)
        header = next(csv_reader)  # Assumes first row is header
        for row in csv_reader:
            # Create a dictionary for each row, removing ".0" from values and adding 'run_id'
            row_dict = {header[i]: value.replace(".0", "") for i, value in enumerate(row)}
            row_dict["run_id"] = run_id
            insert_records.append(row_dict)
    
    # Insert records into the database
    with Session(engine) as session:
        session.execute(insert(table), insert_records)
        session.commit()
    
def run_etl(year: int, engine: sqlalchemy.engine.base.Engine, config: Dict) -> None:
    """
    Runs the ETL process for loading popsim data into the SQL database for a given year.
    
    Parameters:
    - year (int): The year for which data is being loaded.
    - engine (Engine): The SQLAlchemy engine connection.
    - config (dict): Configuration dictionary containing database and ETL process information.
    """
    run_id = get_next_run_id(engine, config)
    
    # load the user to the metadata
    with engine.connect() as conn:
        result = conn.execute(sql.text("SELECT USER_NAME() as username"))
        user = result.first()[0].split("\\")[1] 

    # Adding run metadata to the [metadata].[run] table
    run_metadata = {
        'run_id': run_id,
        'year': year,
        'user': user,
        'date': pd.Timestamp.now(),
        'version': config['version'],
        'comments': config['comments'],
        'loaded': 0
    }
    load_to_sql(df=pd.DataFrame([run_metadata]), 
                name='run', 
                con=engine, 
                schema='metadata')
    print('metadata is loaded')

    # Non-simple ETL Tasks
    etl_controls_csv(run_id=run_id, 
                     filepath = 'populationsim/configs/controls.csv', 
                     engine = engine, 
                     table_name='controls',
                     schema='inputs')
    print('controls is loaded')

    etl_final_summary(engine=engine, 
                      run_id=run_id, 
                      year=year, 
                      transformations_func = sub_geography_summary_manipulations, 
                      input_path='final_summary_mgra.csv', 
                      output_table='control_totals', 
                      schema='outputs',
                      config=config)
    print('final_summary_mgra is loaded')
    etl_final_summary(engine=engine, 
                      run_id=run_id, 
                      year=year, 
                      transformations_func = sub_geography_summary_manipulations, 
                      input_path='final_summary_mgra_PUMA.csv', 
                      output_table='control_totals', 
                      schema='outputs',
                      config=config)
    print('final_summary_mgra_PUMA is loaded')
    etl_final_summary(engine=engine, 
                      run_id=run_id, 
                      year=year, 
                      transformations_func = region_summary_transformations, 
                      input_path='final_summary_region_1.csv', 
                      output_table='control_totals', 
                      schema='outputs',
                      config=config)
    print('final_summary_region_1 is loaded')
    
    # Simple file ETL tasks
    file_mapping = {
        'populationsim/data/seed_households_hh.csv': ['inputs', 'seed_households'],
        'populationsim/data/seed_households_gq.csv': ['inputs', 'seed_households'],
        'populationsim/data/seed_persons_hh.csv': ['inputs', 'seed_persons'],
        'populationsim/data/seed_persons_gq.csv': ['inputs', 'seed_persons'],
        f'output/{year}/synthetic_households_{year}.csv': ['outputs', 'households'],
        f'output/{year}/synthetic_persons_{year}.csv': ['outputs', 'persons'],
        f'output/{year}/mgra15_based_input_{year}.csv': ['outputs', 'mgra_based_input'],
                }
    for path in file_mapping.keys():
        load_simple_files_to_sql(engine=engine, 
                            csv_path=path.replace('year', str(year)), 
                            run_id=run_id, 
                            schema=file_mapping[path][0], 
                            table_name=file_mapping[path][1])
        print(f"{path} is outputted")

    # Update the 'loaded' status to 1 after all ETL tasks are complete
    with engine.connect() as conn:
        sql_command = sql.text(f"UPDATE {config['sql']['output_database']}.[metadata].[run] SET loaded = 1 WHERE run_id = {run_id}")
        conn.execute(sql_command)
        conn.commit()