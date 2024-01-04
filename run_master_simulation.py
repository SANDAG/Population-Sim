# This works for both running in VScode and Terminal 
import os
import shutil
import subprocess
import logging
import yaml
import sys
sys.path.insert(1, 'python')
from create_mgra_controls import build_mgra_control
from create_region_controls import build_region_control

# If the working directory is in the python folder, move up a folder
if os.path.basename(os.getcwd()) == 'python':
    os.chdir('..')

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_simulation():
    try:
        # Change to the correct directory
        os.chdir("populationsim")
        
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
        base_path = "populationsim/output"
        post_process_path = f"output/{year}"

        if not os.path.exists(post_process_path):
            os.makedirs(post_process_path)
        
        # Move standard output files
        shutil.move(f"{base_path}/synthetic_households.csv", f"{post_process_path}/synthetic_households.csv")
        shutil.move(f"{base_path}/synthetic_persons.csv", f"{post_process_path}/synthetic_persons.csv")
        shutil.move(f"{base_path}/timing_log.csv", f"{post_process_path}/timing_log.csv")
        logging.info(f"Standard outputs organized for {year}")

        # Adjusted paths for the GQ output
        gq_base_path = "populationsim/output_gq"

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
        os.chdir('python') 
        build_mgra_control(year) # Build mgra controls 
        build_region_control(year) # Build region controls 
        print(f"{year} controls have been built and loaded to PopSim.")
    finally:
        os.chdir(current_dir) # Change back to the top folder 
    run_simulation()
    organize_outputs(year)

print(f"Outputs for {staging_table} are complete")
logging.info("All years processed successfully.")



