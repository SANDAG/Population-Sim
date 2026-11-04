"""Reporting benchmarks that do not participate in population fitting."""

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
    """Evaluate reporting-only expressions against the configured synthetic population."""
    benchmarks = definitions.loc[
        definitions["population"].notna()
        & ~(
            definitions["geography"].eq("region")
            & definitions["target"].isin(reported_targets)
        )
    ]
    if benchmarks.empty:
        return pd.DataFrame()

    targets_by_geography = {}
    for geography in benchmarks["geography"].unique():
        targets_path = run_dir / f"{geography}_controls.csv"
        targets_by_geography[geography] = (
            pd.read_csv(targets_path) if targets_path.exists() else pd.DataFrame()
        )
    households_path = run_dir / "synthetic_households.csv"
    persons_path = run_dir / "synthetic_persons.csv"
    populations = {}
    if households_path.exists():
        households = pd.read_csv(households_path)
        populations["households"] = households
        if persons_path.exists():
            persons = pd.read_csv(persons_path, dtype={"NAICS2": str}).merge(
                households[["household_id", "gq_type"]],
                on="household_id",
                how="left",
                validate="many_to_one",
            )
            if persons["gq_type"].isna().any():
                raise ValueError("Synthetic persons have missing household/GQ classifications")
            populations["persons"] = persons

    rows = []
    for definition in benchmarks.itertuples(index=False):
        geography = definition.geography
        targets = targets_by_geography[geography]
        control_values = pd.Series(dtype=float)
        if definition.control_field in targets:
            control_values = targets.set_index(geography)[definition.control_field]
            if control_values.index.has_duplicates:
                raise ValueError(f"Expected at most one benchmark row per {geography}")
        results = pd.Series(dtype=float)
        population = populations.get(definition.population)
        if population is not None:
            matches = pd.eval(
                definition.expression,
                local_dict={definition.seed_table: population},
                engine="python",
            )
            if geography == "region":
                results = pd.Series({1: int(matches.sum())})
            else:
                results = matches.groupby(population[geography]).sum()
        ids = (
            pd.Index([1]) if geography == "region"
            else control_values.index.union(results.index)
        )
        for geography_id in ids:
            rows.append({
                "control_id": definition.control_id,
                "control_field": definition.control_field,
                "geography": geography,
                "id": geography_id,
                "control_value": control_values.get(geography_id, float("nan")),
                "result": results.get(
                    geography_id, 0 if population is not None else float("nan")
                ),
                "Status": "Benchmark Only",
            })
    return pd.DataFrame(rows)