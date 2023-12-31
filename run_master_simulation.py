# This works for both running in VScode and Terminal 
import os
import shutil
import subprocess
import logging
import yaml
import sys
print(os.getcwd())
sys.path.insert(1, 'python')
from create_mgra_base import process_yearly_data

# If the working directory is in the python folder, move up a folder
if os.path.basename(os.getcwd()) == 'python':
    os.chdir('..')

print(os.getcwd())


# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def prepare_data(year):
    try:
        # Adjusted paths
        mgra_src = f"1. Getting Data/outputs/mgra_control_{year}.csv"
        region_src = f"1. Getting Data/outputs/region_controls_ind_{year}.csv"
        
        mgra_dest = "2. Implementation/data/mgra_controls.csv"
        region_dest = "2. Implementation/data/region_controls.csv"

        shutil.copy(mgra_src, mgra_dest)
        shutil.copy(region_src, region_dest)
        logging.info(f"Data prepared for {year}")
    except Exception as e:
        logging.error(f"Error preparing data for {year}: {e}")


def run_simulation():
    try:
        # Change to the correct directory
        os.chdir("2. Implementation")
        
        # Run the model
        subprocess.call("python run_populationsim.py -c configs_mp -c configs", shell=True)
        
        # Change back to the original directory
        os.chdir("..")
        
        logging.info("Simulation run successfully")
    except Exception as e:
        logging.error(f"Error running simulation: {e}")


def organize_outputs(year):
    try:
        # Adjusted paths for the standard output
        base_path = "2. Implementation/output"
        post_process_path = f"3. Post_processing/{year}"

        if not os.path.exists(post_process_path):
            os.makedirs(post_process_path)
        
        # Move standard output files
        shutil.move(f"{base_path}/synthetic_households.csv", f"{post_process_path}/synthetic_households.csv")
        shutil.move(f"{base_path}/synthetic_persons.csv", f"{post_process_path}/synthetic_persons.csv")
        shutil.move(f"{base_path}/timing_log.csv", f"{post_process_path}/timing_log.csv")
        logging.info(f"Standard outputs organized for {year}")

        # Adjusted paths for the GQ output
        gq_base_path = "2. Implementation/output_gq"

        # Move GQ output files
        shutil.move(f"{gq_base_path}/synthetic_households_gq.csv", f"{post_process_path}/synthetic_households_gq.csv")
        shutil.move(f"{gq_base_path}/synthetic_persons_gq.csv", f"{post_process_path}/synthetic_persons_gq.csv")
        logging.info(f"GQ outputs organized for {year}")

    except Exception as e:
        logging.error(f"Error organizing outputs for {year}: {e}")

# Get Data From YML File 
with open('config.yml', 'r') as file:
    config = yaml.safe_load(file)
years = config['years']
staging_table = config['staging']['table']

# Store current directory 
current_dir = os.getcwd()

for year in years:
    try:
        os.chdir('python') # the process_yearly_data function needs to be in the python folder (I can change this later)
        process_yearly_data(year) #Run mgra base
    finally:
        os.chdir(current_dir) # Change back to the top folder 
    prepare_data(year)
    run_simulation()
    organize_outputs(year)

print(f"Outputs for {staging_table} is complete")
logging.info("All years processed successfully.")



