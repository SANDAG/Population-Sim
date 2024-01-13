# SANDAG PopulationSim Repository

## Introduction

This repository is dedicated to running PopulationSim, a powerful demographic simulation tool used by SANDAG. PopulationSim is well-suited for generating detailed household and person-level synthetic populations based on sample data and control totals. It is a important component in urban planning and transportation modeling. Learn more about PopulationSim in its [official documentation](https://activitysim.github.io/populationsim/).

## Getting Started

### Prerequisites

Before running PopulationSim, ensure you have the following prerequisites:

1. **Anaconda:** Download and install Anaconda from [here](https://www.anaconda.com/). It will manage the Python environment and packages needed to run PopulationSim.
2. **ODBC Drivers:** To connect to your database, ensure the appropriate ODBC drivers are installed:
   - Press `Win + R` to open the Run dialog.
   - Type `odbcad32` and press Enter to open the ODBC Data Source Administrator.
   - Check the "Drivers" tab to see the list of installed ODBC drivers.
   - Take note of the Driver number you have

### Setting Up the Repository

1. **Clone the Repository:** Ensure the repository is named "Population-Sim" on your local machine.
2. **Update the `config.yml` Document:**
   - Verify the database connection details.
   - Set the staging table to the appropriate SQL table for running PopulationSim.
   - Specify the years for which you wish to run PopulationSim.
3. **Prepare the Data Folder:**
   - The data folder should contain "Labor Force Components.xlsx" and "Summary Forecast Production.xlsx" provided by the economics team.
   - Ensure numeric columns in Excel are set to the "number" category to retain decimal precision.

### Running PopulationSim

Follow these steps to run PopulationSim:

1. **Create a Python Environment:**
   - Open Anaconda Prompt and run: `conda create -n popsim python=3.8`.
   - Activate the environment: `activate popsim`.
   - For further use, no need to create an environment every time, just do `activate popsim`
2. **Install Required Packages:**
   - Install tables support: `conda install pytables`.
   - Install PopulationSim: `pip install populationsim`.
   - Install pyodbc: `pip install pyodbc`.
   - Install openpyxl: `pip install openpyxl`.
3. **Run the Simulation:**
   - Navigate to the repository's location on your computer.
   - Execute: `python run_master_simulation`.
   - The simulation will run, and duration will vary based on your computer's compute power.

### Post-Simulation Steps

1. **Check Outputs:**
   - Once completed, the output folder will contain subfolders for each specified year with the PopulationSim outputs.
2. **Prepare Files for the Transportation Modeling Team:**
   - Run `abm_file_prep.py` inside the python folder.
   - The `abm_output` folder will contain ABM outputs for each year, ready for the ABM team.
3. **Update Version Tracker:**
   - If running PopulationSim for the transportation modeling team, update the version tracker at "T:\socioec\Current_Projects\SR15\S0\version_history.xlsx".
