import pandas as pd
import sqlalchemy as sql
from sqlalchemy.orm import Session
from sqlalchemy import insert
import yaml
import os

def region_summary_transformations(df):
    df = df[['control_name', 'control_value', 'mgra_integer_weight']]
    df.insert(0, 'geography', 'region')
    df.insert(1, 'id', 1)
    df.columns = ['geography', 'id', 'target', 'control', 'result']
    return df

def sub_geography_summary_manipulations(df):
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

def create_engine_from_config(config_path):
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
    engine = sql.create_engine(f"mssql+pymssql://{config['sql']['server']}/")
    return engine, config

def get_next_run_id(engine):
    query = sql.text("SELECT MAX(run_id) as max_run_id FROM [ws].[metadata].[run]")
    with engine.connect() as connection:
        result = connection.execute(query).scalar()
        return result + 1 if result else 1

def add_run_id(df, run_id):
    df.insert(0, 'run_id', run_id)
    return df

def generate_control_id_mapping(engine, run_id):
    query = sql.text(f"SELECT control_id, target FROM [ws].[inputs].[controls] WHERE run_id = {run_id}")
    with engine.connect() as connection:
        result = connection.execute(query)
        rows = result.fetchall()
        control_id_mapping = {row[1]: row[0] for row in rows}
        return control_id_mapping

def add_control_id(df, engine, run_id, control_column='target'):
    # Assign control_id based on the provided mapping
    control_id_mapping = generate_control_id_mapping(engine, run_id)
    df['control_id'] = df[control_column].map(control_id_mapping)
    return df[df['control_id'].notnull()]

def load_to_sql(df, name, con, schema):
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

def etl_controls_csv(run_id, filepath, engine, table_name, schema):
    df = pd.read_csv(filepath)
    df = add_run_id(df, run_id)
    df['control_id'] = range(1, len(df) + 1)
    load_to_sql(df=df, name=table_name, con=engine, schema=schema)

def etl_final_summary(engine, run_id, year, transformations_func, input_path, output_table, schema):
    df = pd.read_csv(f'output/{year}/{input_path}')
    df = transformations_func(df)
    df = add_run_id(df, run_id)
    df = add_control_id(df, engine, run_id, control_column='target')
    df = df.rename(columns={'id': 'geography_id', 'control':'control_value'})
    df = df[['run_id', 'geography', 'geography_id', 'control_id', 'control_value', 'result']]
    load_to_sql(df=df, name=output_table, con=engine, schema=schema)

seed_persons_dtype_dict = {
    'PUMA': 'Int64', 
    'SEX': 'Int64',
    'ESR': 'Int64',
    'COW': 'Int64',
    'SCHG': 'Int64',
    'RAC1P': 'Int64',
    'MIL': 'Int64',
    'SCHL': 'Int64',
    'OCCP': 'Int64',
    'WKW': 'Int64',
    'SOC2': 'Int64'
}
output_households_dtype_dict = {
    'HHT': 'Int64', 
    'HUPAC': 'Int64',
    'VEH': 'Int64',
    'BLD': 'Int64',
}

def etl_simple_files(run_id, file_mapping, year, engine):
    for filepath, table_info in file_mapping.items():
        if 'persons' in filepath:
            df = pd.read_csv(filepath.replace('year', str(year)), dtype=seed_persons_dtype_dict)
        elif 'synthetic_households':
            df = pd.read_csv(filepath.replace('year', str(year)), dtype=output_households_dtype_dict)
        else:
            df = pd.read_csv(filepath.replace('year', str(year)))
        df = add_run_id(df, run_id)
        with engine.begin() as conn: 
            load_to_sql(df=df, name=table_info[1], con=conn, schema=table_info[0])
        print(f"{filepath} is uploaded")
    
def run_etl(year, config_path='config.yml'):
    engine, config = create_engine_from_config(config_path)
    run_id = get_next_run_id(engine)
    
    # load the user to the metadata
    with engine.connect() as conn:
        result = conn.execute(sql.text("SELECT USER_NAME() as username"))
        user = result.first()[0].split("\\")[1] 

    # Adding run metadata to the [ws].[metadata].[run] table
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
                      schema='outputs')
    print('final_summary_mgra is loaded')
    etl_final_summary(engine=engine, 
                      run_id=run_id, 
                      year=year, 
                      transformations_func = sub_geography_summary_manipulations, 
                      input_path='final_summary_mgra_PUMA.csv', 
                      output_table='control_totals', 
                      schema='outputs')
    print('final_summary_mgra_PUMA is loaded')
    etl_final_summary(engine=engine, 
                      run_id=run_id, 
                      year=year, 
                      transformations_func = region_summary_transformations, 
                      input_path='final_summary_region_1.csv', 
                      output_table='control_totals', 
                      schema='outputs')
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
    etl_simple_files(run_id, 
                     file_mapping, 
                     year, 
                     engine)

    # Update the 'loaded' status to 1 after all ETL tasks are complete
    with engine.connect() as conn:
        sql_command = sql.text(f"UPDATE [ws].[metadata].[run] SET loaded = 1 WHERE run_id = {run_id}")
        conn.execute(sql_command)
        conn.commit()