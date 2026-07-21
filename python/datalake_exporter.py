"""
Exports PopulationSim CSV output files to Azure Data Lake Storage as Parquet files.

Reads all CSVs from the specified output directory, converts them to Parquet,
and uploads them to the datalake under popsim/<file>/<year>/<file>_<timestamp>.parquet.
where <year> is the last segment of the output_path (e.g. '2022').
The timestamp is derived from the modification time of synthetic_persons.csv.

This layout lets Databricks Autoloader / Spark Declarative Pipelines point at
popsim/<file>/ and ingest all runs for a given table across years.
"""

import datetime
import glob
import json
import os
import re
import sys
from io import BytesIO

import pandas as pd
from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import ContainerClient

# -----------------------------------------------------------------------
# HOW TO RUN
# -----------------------------------------------------------------------
#   Activate the sandag-population-sim venv
#   Usage:          python datalake_exporter.py <output_path> <env>
#   Example (dev):  python datalake_exporter.py C:\abm_runs\popsim_new\output\2022 dev
#   Example (prod): python datalake_exporter.py C:\abm_runs\popsim_new\output\2022 prod
#
# Notes:
#   - env must be 'dev' or 'prod'
#   - output_path must contain synthetic_persons.csv
#   - CSVs are converted to parquet and uploaded to: popsim/<file>/<year>/<file>_<timestamp>.parquet
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
        print(
            f"{e}: popsim exporter could not find SAS token in environment\n",
            file=sys.stderr,
        )
        return False, None
    except Exception as e:
        print(
            f"{e}: popsim exporter could not connect to Azure container\n",
            file=sys.stderr,
        )
        return False, None


def build_blob_path(*parts):
    return "/".join(filter(None, parts))


def get_lake_name(name):
    # mgra15_based_input is the only output file with a year suffix baked into its
    # name (e.g. "mgra15_based_input_2035"); strip it so every year lands under one
    # lake path. 
    return re.sub(r"^mgra15_based_input_\d{4}$", "mgra15_based_input", name)


def export_csv_as_parquet(file, folder_name, ts_str, container, run_timestamp=None):
    table = pd.read_csv(file, low_memory=False)
    # year and run_timestamp are added as columns (not just encoded in the blob path) so
    # Autoloader/Spark can partition and query across runs without parsing the file path.
    if folder_name.isdigit():
        table["year"] = int(folder_name)
    if run_timestamp is not None:
        table["run_timestamp"] = run_timestamp
    name = os.path.splitext(os.path.basename(file))[0]
    lake_name = get_lake_name(name)
    lake_file_name = build_blob_path(
        "popsim", lake_name, folder_name, lake_name + "_" + ts_str + ".parquet"
    )
    parquet_file = BytesIO()
    table.to_parquet(parquet_file, engine="pyarrow")
    parquet_file.seek(0)
    t0 = datetime.datetime.now()
    try:
        container.upload_blob(name=lake_file_name, data=parquet_file)
        elapsed = (datetime.datetime.now() - t0).total_seconds()
        print(f"{lake_name} took {elapsed:.1f}s to write to Azure")
        return True
    except ResourceExistsError:
        print(f"{lake_file_name} already exists in Azure, skipping", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Failed to upload {lake_name}: {e}", file=sys.stderr)
        return False


def write_to_datalake(output_path, env, metadata=None):
    if not os.path.isdir(output_path):
        print(
            f"Output path does not exist or is not a directory: {output_path}",
            file=sys.stderr,
        )
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

    succeeded = []
    failed = []
    for file in files:
        ok = export_csv_as_parquet(
            file, folder_name, ts_str, container, run_timestamp=created_ts
        )
        (succeeded if ok else failed).append(os.path.basename(file))

    if metadata is not None:
        meta_df = pd.DataFrame([metadata])
        meta_blob = build_blob_path(
            "popsim", "run_metadata", folder_name, "run_metadata_" + ts_str + ".parquet"
        )
        parquet_file = BytesIO()
        meta_df.to_parquet(parquet_file, engine="pyarrow")
        parquet_file.seek(0)
        try:
            container.upload_blob(name=meta_blob, data=parquet_file)
            succeeded.append("run_metadata.parquet")
            print("run_metadata.parquet written to Azure")
        except ResourceExistsError:
            print(f"{meta_blob} already exists in Azure, skipping", file=sys.stderr)
            failed.append("run_metadata.parquet")
        except Exception as e:
            print(f"Failed to upload run_metadata: {e}", file=sys.stderr)
            failed.append("run_metadata.parquet")

    print(f"\nExport complete: {len(succeeded)} succeeded, {len(failed)} failed")
    if failed:
        print(f"Failed files: {', '.join(failed)}", file=sys.stderr)


if __name__ == "__main__":
    import yaml

    if len(sys.argv) < 3:
        print(
            "Usage: python datalake_exporter_popsim.py <output_path> <env>",
            file=sys.stderr,
        )
        print("  env must be 'dev' or 'prod'", file=sys.stderr)
        sys.exit(1)
    output_path = sys.argv[1]
    env = sys.argv[2].lower()
    if env not in {"dev", "prod"}:
        print(
            f"Error: env must be 'dev' or 'prod', got '{sys.argv[2]}'", file=sys.stderr
        )
        sys.exit(1)

    # Build run_metadata from every top-level field in config.yml, plus the run year
    # parsed from the output folder name. Nested/list fields (sql, synthesis_runs, years)
    # are JSON-encoded so pandas/pyarrow can serialize them as flat string columns in the
    # run_metadata parquet file. Skip metadata entirely if config.yml is missing/invalid.
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yml")
    metadata = None
    try:
        with open(config_path, "r") as f:
            cfg = yaml.safe_load(f)
        metadata = {
            "year": int(year_str)
            if (year_str := os.path.basename(output_path)).isdigit()
            else year_str,
        }
        for key, value in cfg.items():
            metadata[key] = json.dumps(value) if isinstance(value, (dict, list)) else value
    except Exception as e:
        print(
            f"Could not load config.yml, run_metadata will be skipped: {e}",
            file=sys.stderr,
        )

    write_to_datalake(output_path, env, metadata=metadata)
