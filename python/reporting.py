"""Reporting benchmarks that do not participate in population fitting."""

import json
from pathlib import Path

import pandas as pd


def load_control_definitions(run_dir: Path, configs_dir: Path) -> pd.DataFrame:
    """Prefer the run's archived definitions over current configurations."""
    active_path = run_dir / "controls.csv"
    if not active_path.exists():
        active_path = configs_dir / "controls.csv"
    active = pd.read_csv(active_path)
    benchmark_path = run_dir / "reporting_controls.csv"
    if not benchmark_path.exists():
        benchmark_path = configs_dir / "reporting_controls.csv"
    benchmarks = pd.read_csv(benchmark_path)
    definitions = pd.concat([active, benchmarks], ignore_index=True)
    definitions = definitions.drop_duplicates("target", keep="first").reset_index(drop=True)
    definitions["control_id"] = range(1, len(definitions) + 1)
    return definitions


def get_benchmark_comparisons(
    run_dir: Path, definitions: pd.DataFrame, reported_targets: set
) -> pd.DataFrame:
    """Evaluate reporting-only filters against the configured synthetic population."""
    benchmarks = definitions.loc[
        definitions["filters"].notna()
        & ~definitions["target"].isin(reported_targets)
    ]
    if benchmarks.empty:
        return pd.DataFrame()

    targets_path = run_dir / "region_controls.csv"
    targets = pd.read_csv(targets_path) if targets_path.exists() else pd.DataFrame()
    households_path = run_dir / "synthetic_households.csv"
    persons_path = run_dir / "synthetic_persons.csv"
    populations = {}
    if households_path.exists():
        households = pd.read_csv(households_path)
        populations["households"] = households
        if persons_path.exists():
            persons = pd.read_csv(persons_path).merge(
                households[["household_id", "gq_type"]],
                on="household_id",
                how="left",
                validate="many_to_one",
            )
            if persons["gq_type"].isna().any():
                raise ValueError("Synthetic persons have missing household/GQ classifications")
            populations["persons"] = persons

    def _matches(frame: pd.DataFrame, filters: list[dict]) -> pd.Series:
        matches = pd.Series(True, index=frame.index)
        for condition in filters:
            column = condition["column"]
            if column not in frame:
                raise ValueError(f"Reporting filter references unavailable field {column!r}")
            series = frame[column]
            values = condition["values"]
            if pd.api.types.is_numeric_dtype(series.dtype):
                values = pd.to_numeric(pd.Series(values), errors="raise").tolist()
            operator_name = condition["operator"]
            if operator_name == "eq":
                match = series == values[0]
            elif operator_name == "ne":
                match = series != values[0]
            elif operator_name == "in":
                match = series.isin(values)
            elif operator_name == "gt":
                match = series > values[0]
            elif operator_name == "ge":
                match = series >= values[0]
            elif operator_name == "lt":
                match = series < values[0]
            elif operator_name == "le":
                match = series <= values[0]
            else:
                raise ValueError(f"Unsupported reporting filter operator {operator_name!r}")
            matches &= series.notna() & match
        return matches

    rows = []
    for definition in benchmarks.itertuples(index=False):
        control_value = float("nan")
        if definition.control_field in targets:
            values = targets.loc[targets["region"] == 1, definition.control_field]
            if len(values) > 1:
                raise ValueError("Expected at most one regional benchmark row")
            if len(values) == 1:
                control_value = values.iloc[0]
        result = float("nan")
        population = populations.get(definition.population)
        if population is not None:
            filters = json.loads(definition.filters)
            result = int(_matches(population, filters).sum())
        rows.append({
            "control_id": definition.control_id,
            "control_field": definition.control_field,
            "geography": "region",
            "id": 1,
            "control_value": control_value,
            "result": result,
            "Status": "Benchmark Only",
        })
    return pd.DataFrame(rows)