"""
Exports PopulationSim CSV output files to Azure Data Lake Storage as Parquet files.

Reads all CSVs from the specified output directory, converts them to Parquet,
and uploads them to the datalake under popsim/<file>/<year>/<file>_<timestamp>.parquet.
where <year> is the last segment of the output_path (e.g. '2022').
The timestamp is derived from the modification time of synthetic_persons.csv.

Each synthesis run's controls.csv (control definitions) lives under
populationsim/configs*/ rather than in the output directory, so it isn't
picked up by the CSV glob. It's exported separately via controls_paths,
landing under popsim/controls/<year>/... (household) or
popsim/controls_<run>/<year>/... (GQ runs).

This layout lets Databricks Autoloader / Spark Declarative Pipelines point at
popsim/<file>/ and ingest all runs for a given table across years.
A completion marker is written last, to popsim/_export_status/<year>/, once
every other file for the run has been attempted to kick off a pipeline
update only after a run's export has fully finished."""

import datetime
import getpass
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
# HOW TO RUN AFTER POPSIM GENERATES OUTPUT
# -----------------------------------------------------------------------
#   Activate the sandag-population-sim venv
#   Usage:          python datalake_exporter.py <output_path> <env> [--batch-id <id>]
#   Example (dev):  python datalake_exporter.py C:\abm_runs\popsim_new\output\2022 dev
#   Example (prod): python datalake_exporter.py C:\abm_runs\popsim_new\output\2022 prod
#   Example (add to an existing batch):
#                   python datalake_exporter.py C:\abm_runs\popsim_new\output\2026 dev --batch-id 20260927_143005
#
# Notes:
#   - env must be 'dev' or 'prod'
#   - output_path must contain synthetic_persons.csv
#   - batch_id defaults to a new timestamp (the export becomes its own batch)
#   - CSVs are converted to parquet and uploaded to: popsim/<file>/<year>/<file>_<timestamp>.parquet
# -----------------------------------------------------------------------


def connect_to_azure(env):
    try:
        if env == "dev":
            sas_url = os.environ["AZURE_STORAGE_SAS_TOKEN_DS_DEV_SHARED"]
        elif env == "prod":
            sas_url = os.environ["AZURE_STORAGE_SAS_TOKEN_DS_PROD_SHARED"]
        else:
            raise ValueError(f"env must be 'dev' or 'prod', got {env!r}")
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


def new_batch_id():
    """Identifier shared by every year exported from one execution, so runs
    that were produced together can be grouped in run_info (batch_id column)."""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def build_run_metadata(year, config, batch_id):
    """run_metadata row for one exported year: year, batch_id, the Windows
    login running the export (user, like the old metadata.run table), plus every
    top-level field in config.yml. Nested/list fields (sql, synthesis_runs,
    years) are JSON-encoded so pandas/pyarrow can serialize them as flat
    string columns in the run_metadata parquet file."""
    metadata = {"year": year, "batch_id": batch_id, "user": getpass.getuser()}
    for key, value in config.items():
        metadata[key] = json.dumps(value) if isinstance(value, (dict, list)) else value
    return metadata


def build_blob_path(*parts):
    return "/".join(filter(None, parts))


def get_lake_name(name):
    # mgra15_based_input is the only output file with a year suffix baked into its
    # name (e.g. "mgra15_based_input_2035"); strip it so every year lands under one
    # lake path. 
    return re.sub(r"^mgra15_based_input_\d{4}$", "mgra15_based_input", name)


def export_csv_as_parquet(file, folder_name, ts_str, container, run_timestamp=None):
    name = os.path.splitext(os.path.basename(file))[0]
    lake_name = get_lake_name(name)
    try:
        table = pd.read_csv(file, low_memory=False)
        # year and run_timestamp are added as columns (not just encoded in the blob path) so
        # Autoloader/Spark can partition and query across runs without parsing the file path.
        if folder_name.isdigit():
            table["year"] = int(folder_name)
        if run_timestamp is not None:
            table["run_timestamp"] = run_timestamp
        lake_file_name = build_blob_path(
            "popsim", lake_name, folder_name, lake_name + "_" + ts_str + ".parquet"
        )
        parquet_file = BytesIO()
        table.to_parquet(parquet_file, engine="pyarrow")
        parquet_file.seek(0)
        t0 = datetime.datetime.now()
        container.upload_blob(name=lake_file_name, data=parquet_file)
        elapsed = (datetime.datetime.now() - t0).total_seconds()
        print(f"{lake_name} took {elapsed:.1f}s to write to Azure")
        return True
    except ResourceExistsError:
        print(f"{lake_file_name} already exists in Azure, skipping", file=sys.stderr)
        return True
    except Exception as e:
        print(f"Failed to upload {lake_name}: {e}", file=sys.stderr)
        return False


def export_controls_csv(filepath, run_name, folder_name, ts_str, container, run_timestamp=None):
    lake_name = "controls" if run_name == "household" else f"controls_{run_name}"
    try:
        table = pd.read_csv(filepath)
        if folder_name.isdigit():
            table["year"] = int(folder_name)
        table["synthesis_run"] = run_name
        # run_timestamp is required to join this file to run_id_lookup (keyed on
        # run_timestamp + year), matching the timestamp stamped on every other
        # export for the same run.
        if run_timestamp is not None:
            table["run_timestamp"] = run_timestamp
        lake_file_name = build_blob_path(
            "popsim", lake_name, folder_name, lake_name + "_" + ts_str + ".parquet"
        )
        parquet_file = BytesIO()
        table.to_parquet(parquet_file, engine="pyarrow")
        parquet_file.seek(0)
        container.upload_blob(name=lake_file_name, data=parquet_file)
        print(f"{lake_name} written to Azure")
        return True
    except ResourceExistsError:
        print(f"{lake_file_name} already exists in Azure, skipping", file=sys.stderr)
        return True
    except Exception as e:
        print(f"Failed to upload {lake_name}: {e}", file=sys.stderr)
        return False


def export_seed_csv(filepath, run_name, seed_type, folder_name, ts_str, container, run_timestamp=None):
    lake_name = f"seed_{seed_type}" if run_name == "household" else f"seed_{seed_type}_{run_name}"
    try:
        table = pd.read_csv(filepath)
        if folder_name.isdigit():
            table["year"] = int(folder_name)
        table["synthesis_run"] = run_name
        if run_timestamp is not None:
            table["run_timestamp"] = run_timestamp
        lake_file_name = build_blob_path(
            "popsim", lake_name, folder_name, lake_name + "_" + ts_str + ".parquet"
        )
        parquet_file = BytesIO()
        table.to_parquet(parquet_file, engine="pyarrow")
        parquet_file.seek(0)
        container.upload_blob(name=lake_file_name, data=parquet_file)
        print(f"{lake_name} written to Azure")
        return True
    except ResourceExistsError:
        print(f"{lake_file_name} already exists in Azure, skipping", file=sys.stderr)
        return True
    except Exception as e:
        print(f"Failed to upload {lake_name}: {e}", file=sys.stderr)
        return False


def find_controls_paths(synthesis_runs, popsim_dir=None):
    # controls.csv lives in whichever config dir a run lists first that
    # actually has one. Resolve it per run rather than hardcoding a directory index.
    if popsim_dir is None:
        popsim_dir = os.path.join(os.path.dirname(__file__), "..", "populationsim")
    controls_paths = {}
    for run in synthesis_runs:
        for c in run["configs"]:
            candidate = os.path.join(popsim_dir, c, "controls.csv")
            if os.path.isfile(candidate):
                controls_paths[run["name"]] = candidate
                break
    return controls_paths


def find_seed_paths(synthesis_runs, popsim_dir=None):
    """Locates each run's seed_households/seed_persons CSVs. Household files
    use an '_hh' suffix while GQ files use the run name directly (see
    main.py's write_seed_files/GQ_TYPES)."""
    if popsim_dir is None:
        popsim_dir = os.path.join(os.path.dirname(__file__), "..", "populationsim")
    seed_paths = {}
    for run in synthesis_runs:
        suffix = "hh" if run["name"] == "household" else run["name"]
        data_dir = os.path.join(popsim_dir, run["data"])
        households_path = os.path.join(data_dir, f"seed_households_{suffix}.csv")
        persons_path = os.path.join(data_dir, f"seed_persons_{suffix}.csv")
        if os.path.isfile(households_path) and os.path.isfile(persons_path):
            seed_paths[run["name"]] = {"households": households_path, "persons": persons_path}
    return seed_paths


def write_completion_marker(folder_name, ts_str, container, succeeded, failed):
    """Written last, after every other file has been attempted for a Databricks 
    file arrival trigger. Overwrittenon retries so it always reflects the most 
    recent attempt for this run."""
    marker = {"succeeded": len(succeeded), "failed": len(failed), "failed_files": failed}
    marker_blob = build_blob_path(
        "popsim", "_export_status", folder_name, "_SUCCESS_" + ts_str + ".json"
    )
    try:
        container.upload_blob(
            name=marker_blob, data=json.dumps(marker).encode("utf-8"), overwrite=True
        )
        print(f"Export completion marker written ({len(succeeded)} succeeded, {len(failed)} failed)")
    except Exception as e:
        print(f"Failed to upload completion marker: {e}", file=sys.stderr)


def write_to_datalake(output_path, env, metadata=None, controls_paths=None, seed_paths=None):
    if not os.path.isdir(output_path):
        print(
            f"Output path does not exist or is not a directory: {output_path}",
            file=sys.stderr,
        )
        return

    cloud_bool, container = connect_to_azure(env)
    if not cloud_bool:
        return

    folder_name = os.path.basename(os.path.normpath(output_path))

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

    # controls.csv definitions live under populationsim/configs*/, not in the
    # output/<year> folder, so they aren't picked up by the glob above.
    for run_name, filepath in (controls_paths or {}).items():
        ok = export_controls_csv(
            filepath, run_name, folder_name, ts_str, container, run_timestamp=created_ts
        )
        label = "controls.csv" if run_name == "household" else f"controls_{run_name}.csv"
        (succeeded if ok else failed).append(label)

    # seed_households/seed_persons live under populationsim/data/, not in the
    # output/<year> folder, so they aren't picked up by the glob above either.
    for run_name, paths in (seed_paths or {}).items():
        for seed_type, filepath in paths.items():
            ok = export_seed_csv(
                filepath, run_name, seed_type, folder_name, ts_str, container, run_timestamp=created_ts
            )
            label = (
                f"seed_{seed_type}.csv"
                if run_name == "household"
                else f"seed_{seed_type}_{run_name}.csv"
            )
            (succeeded if ok else failed).append(label)

    if metadata is not None:
        meta_blob = build_blob_path(
            "popsim", "run_metadata", folder_name, "run_metadata_" + ts_str + ".parquet"
        )
        try:
            meta_df = pd.DataFrame([metadata])
            meta_df["run_timestamp"] = created_ts
            parquet_file = BytesIO()
            meta_df.to_parquet(parquet_file, engine="pyarrow")
            parquet_file.seek(0)
            container.upload_blob(name=meta_blob, data=parquet_file)
            succeeded.append("run_metadata.parquet")
            print("run_metadata.parquet written to Azure")
        except ResourceExistsError:
            print(f"{meta_blob} already exists in Azure, skipping", file=sys.stderr)
            succeeded.append("run_metadata.parquet")
        except Exception as e:
            print(f"Failed to upload run_metadata: {e}", file=sys.stderr)
            failed.append("run_metadata.parquet")

    print(f"\nExport complete: {len(succeeded)} succeeded, {len(failed)} failed")
    if failed:
        print(f"Failed files: {', '.join(failed)}", file=sys.stderr)
        print("Completion marker not written because the export is incomplete", file=sys.stderr)
        return

    write_completion_marker(folder_name, ts_str, container, succeeded, failed)


if __name__ == "__main__":
    import yaml

    if len(sys.argv) < 3:
        print(
            "Usage: python datalake_exporter.py <output_path> <env> [--batch-id <id>]",
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

    # Optional --batch-id groups this export with other years from the same
    # execution (pass the batch_id shown in run_info); without it, the export
    # is its own batch.
    extra_args = sys.argv[3:]
    if not extra_args:
        batch_id = new_batch_id()
    elif len(extra_args) == 2 and extra_args[0] == "--batch-id":
        batch_id = extra_args[1]
    else:
        print(
            f"Error: unexpected arguments {extra_args}; expected [--batch-id <id>]",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"batch_id: {batch_id}")

    # Build run_metadata from config.yml plus the run year parsed from the output
    # folder name. Skip metadata entirely if config.yml is missing/invalid.
    # Resolve config.yml/populationsim relative to output_path's repo root, not
    # this script's location
    # Assumes the standard layout: <repo_root>/output/<year>.
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(output_path)))
    config_path = os.path.join(repo_root, "config.yml")
    popsim_dir = os.path.join(repo_root, "populationsim")
    metadata = None
    cfg = None
    try:
        with open(config_path, "r") as f:
            cfg = yaml.safe_load(f)
        year_str = os.path.basename(output_path)
        metadata = build_run_metadata(
            year=int(year_str) if year_str.isdigit() else year_str,
            config=cfg,
            batch_id=batch_id,
        )
    except Exception as e:
        print(
            f"Could not load config.yml, run_metadata will be skipped: {e}",
            file=sys.stderr,
        )

    controls_paths = {}
    seed_paths = {}
    if cfg is not None:
        controls_paths = find_controls_paths(cfg.get("synthesis_runs", []), popsim_dir)
        seed_paths = find_seed_paths(cfg.get("synthesis_runs", []), popsim_dir)

    write_to_datalake(
        output_path,
        env,
        metadata=metadata,
        controls_paths=controls_paths,
        seed_paths=seed_paths,
    )
