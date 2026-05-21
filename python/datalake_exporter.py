"""
Exports PopulationSim CSV output files to Azure Data Lake Storage as Parquet files.

Reads all CSVs from the specified output directory, converts them to Parquet,
and uploads them to the datalake under popsim/<output_folder>/<timestamp>/.
where <output_folder> is the last segment of the output_path (e.g. '2022').
The timestamp is derived from the modification time of synthetic_persons.csv.
"""

import datetime
import glob
import os
import sys
from io import BytesIO

import pandas as pd
from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import ContainerClient

# -----------------------------------------------------------------------
# HOW TO RUN
# -----------------------------------------------------------------------
# Step 1 — Activate the uv environment in command prompt:
#   C:\uv_env\asim_140\.venv\Scripts\activate
#
# Step 2 — Run the script:
#   Usage:          python datalake_exporter_popsim.py <output_path> <env>
#   Example (dev):  python datalake_exporter_popsim.py C:\abm_runs\popsim_new\output\2022 dev
#   Example (prod): python datalake_exporter_popsim.py C:\abm_runs\popsim_new\output\2022 prod
#
# Notes:
#   - env must be 'dev' or 'prod'
#   - output_path must contain synthetic_persons.csv
#   - CSVs are converted to parquet and uploaded to: popsim/<output_folder>/<timestamp>/
# -----------------------------------------------------------------------

def connect_to_azure(env):
    try:
        if env == "dev":
            sas_url = os.environ["AZURE_STORAGE_SAS_TOKEN_DS_DEV_SHARED"]
        else:
            sas_url = os.environ["AZURE_STORAGE_SAS_TOKEN_DS_PROD_SHARED"]
        container = ContainerClient.from_container_url(sas_url)
        container.get_account_information()
        print("popsim exporter connected to Azure container")
        return True, container
    except KeyError as e:
        print(f"{e}: popsim exporter could not find SAS token in environment\n", file=sys.stderr)
        return False, None
    except Exception as e:
        print(f"{e}: popsim exporter could not connect to Azure container\n", file=sys.stderr)
        return False, None


def build_blob_path(*parts):
    return "/".join(filter(None, parts))


def export_csv_as_parquet(file, blob_path, container):
    table = pd.read_csv(file, low_memory=False)
    name = os.path.splitext(os.path.basename(file))[0]
    lake_file_name = build_blob_path(blob_path, name + ".parquet")
    parquet_file = BytesIO()
    table.to_parquet(parquet_file, engine="pyarrow")
    parquet_file.seek(0)
    t0 = datetime.datetime.now()
    
    try:
        container.upload_blob(name=lake_file_name, data=parquet_file)
        elapsed = (datetime.datetime.now() - t0).total_seconds()
        print(f"{name} took {elapsed:.1f}s to write to Azure")
        return True
    except ResourceExistsError:
        print(f"{lake_file_name} already exists in Azure, skipping", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Failed to upload {name}: {e}", file=sys.stderr)
        return False
    

def write_to_datalake(output_path, env):
    if not os.path.isdir(output_path):
        print(f"Output path does not exist or is not a directory: {output_path}", file=sys.stderr)
        return

    cloud_bool, container = connect_to_azure(env)
    if not cloud_bool:
        return

    folder_name = os.path.basename(output_path)

    files = glob.glob(os.path.join(output_path, "*.csv"))
    if not files:
        print(f"No CSV files found in {output_path}", file=sys.stderr)
        return

    # synthetic_persons.csv is used as a reference file to derive the run timestamp.
    # Its modification time represents when the PopulationSim run completed and is used to
    # version the blob path, so each run's outputs are stored in a unique folder.
    ref_file = os.path.join(output_path, "synthetic_persons.csv")
    if not os.path.isfile(ref_file):
        print(f"synthetic_persons.csv not found in {output_path}", file=sys.stderr)
        return
    created_ts = datetime.datetime.fromtimestamp(os.path.getmtime(ref_file))
    ts_str = created_ts.strftime("%Y%m%d_%H%M%S")
    blob_path = build_blob_path("popsim", folder_name, ts_str)

    succeeded = []
    failed = []
    for file in files:
        ok = export_csv_as_parquet(file, blob_path, container)
        (succeeded if ok else failed).append(os.path.basename(file))

    print(f"\nExport complete: {len(succeeded)} succeeded, {len(failed)} failed")
    if failed:
        print(f"Failed files: {', '.join(failed)}", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python datalake_exporter_popsim.py <output_path> <env>", file=sys.stderr)
        print("  env must be 'dev' or 'prod'", file=sys.stderr)
        sys.exit(1)
    output_path = sys.argv[1]
    env = sys.argv[2].lower()
    if env not in {"dev", "prod"}:
        print(f"Error: env must be 'dev' or 'prod', got '{sys.argv[2]}'", file=sys.stderr)
        sys.exit(1)
    write_to_datalake(output_path, env)