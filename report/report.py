import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from IPython.display import display
import yaml
import streamlit as st
import sqlalchemy as sql
import os
from pathlib import Path
from datetime import datetime
import re

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from python.db import get_engine

@st.cache_data
def build_scatter_plot(
    df: pd.DataFrame, y_var: str, hover_data: str, title: str
) -> px.scatter:
    """Build Control Scatter plot for a given control."""
    fig = px.scatter(
        data_frame=df,
        x="Control",
        y=y_var,
        hover_data=hover_data,
        title=title,
    )

    fig.update_traces(marker=dict(size=12))
    fig.add_hline(y=0, line_dash="dash", line_color="black")

    return fig


@st.cache_data
def get_control_data(run_id: str, _sql_engine: sql.engine) -> pd.DataFrame:
    with _sql_engine.connect() as connection:
        with open("./report/controls.sql", "r") as query:
            return pd.read_sql_query(
                sql.text(query.read().format(run_id=run_id)),
                connection,
            )


@st.cache_data
def get_run_metadata(_sql_engine: sql.engine) -> pd.DataFrame:
    with _sql_engine.connect() as connection:
        with open("./report/metadata.sql", "r") as query:
            return pd.read_sql_query(
                sql.text(query.read()),
                connection,
            )


@st.cache_data
def get_local_run_metadata(output_dir: str = "./output") -> pd.DataFrame:
    """
    Scan output directory for local runs and build metadata DataFrame.

    Each subdirectory of output_dir is one run — the directory name is used
    directly as the run identifier and does not need to be a bare year
    (e.g. "2022", "2022_sc1", "2022_scn2" are all valid), so multiple
    scenario runs for the same year can coexist and be browsed separately.
    """
    local_runs = []

    if not os.path.exists(output_dir):
        return pd.DataFrame(columns=["run_id", "folder", "year", "date", "version", "source"])

    for folder in sorted(os.listdir(output_dir)):
        folder_path = os.path.join(output_dir, folder)
        if not os.path.isdir(folder_path):
            continue

        timing_log = os.path.join(folder_path, "timing_log.csv")
        synthetic_hh = os.path.join(folder_path, "synthetic_households.csv")
        synthetic_persons = os.path.join(folder_path, "synthetic_persons.csv")

        if all(os.path.exists(f) for f in [timing_log, synthetic_hh, synthetic_persons]):
            mod_time = datetime.fromtimestamp(os.path.getmtime(timing_log))

            # Pull a leading 4-digit year for display/sorting if present
            # ("2022_sc1" -> "2022"); fall back to the raw folder name.
            year_match = re.match(r"^(\d{4})", folder)
            year_display = year_match.group(1) if year_match else folder

            local_runs.append({
                "run_id": f"{folder}_local",
                "folder": folder,       # actual path segment, used downstream
                "year": year_display,   # display only
                "date": mod_time.strftime("%Y-%m-%d %H:%M"),
                "version": "local",
                "source": "local",
            })

    return pd.DataFrame(local_runs)

def _melt_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Reshape a PopulationSim summary file (wide, one _control/_result
    column pair per target) into long form: one row per geography/id/target."""
    control_cols = [c for c in df.columns if c.endswith("_control")]
    result_cols = [c for c in df.columns if c.endswith("_result")]
    df_control = df.melt(id_vars=["geography", "id"], value_vars=control_cols,
                          var_name="target", value_name="control_value")
    df_result = df.melt(id_vars=["geography", "id"], value_vars=result_cols,
                         var_name="target", value_name="result")
    df_control["target"] = df_control["target"].str.replace("_control", "")
    df_result["target"] = df_result["target"].str.replace("_result", "")
    merged = pd.merge(df_control, df_result, on=["geography", "id", "target"])
    merged["geography"] = merged["geography"].str.lower()
    return merged

@st.cache_data
def get_control_data_from_local(run_folder: str) -> pd.DataFrame:
    """
    Load control data from local CSV files.

    Parameters
    ----------
    run_folder : str
        The output subdirectory name for this run (e.g. "2022", "2022_sc1"),
        used directly as the path segment under ./output/.
    """
    # Household controls — target names here are assumed unique to household
    controls_df = pd.read_csv("./populationsim/configs/controls.csv")
    controls_df["control_id"] = range(1, len(controls_df) + 1)
    next_id = len(controls_df) + 1

    all_rows = []

    # --- Household: mgra / PUMA ---
    household_summary_files = {
        "mgra": f"./output/{run_folder}/final_summary_mgra.csv",
        "PUMA": f"./output/{run_folder}/final_summary_mgra_PUMA.csv",
    }
    for path in household_summary_files.values():
        if os.path.exists(path):
            melted = _melt_summary(pd.read_csv(path))
            melted = melted.merge(
                controls_df[["control_id", "target", "control_field"]],
                on="target", how="left",
            )
            all_rows.append(melted[["control_id", "control_field", "geography", "id", "control_value", "result"]])

    # --- Household: region ---
    region_path = f"./output/{run_folder}/final_summary_region_1.csv"
    if os.path.exists(region_path):
        df = pd.read_csv(region_path)
        df = df[["control_name", "control_value", "mgra_integer_weight"]]
        df.insert(0, "geography", "region")
        df.insert(1, "id", 1)
        df.columns = ["geography", "id", "target", "control_value", "result"]
        df = df.merge(controls_df[["control_id", "target", "control_field"]], on="target", how="left")
        all_rows.append(df[["control_id", "control_field", "geography", "id", "control_value", "result"]])

    # --- GQ: each type's summary only ever has a "Total_GQ" target — that
    # name is reused identically across all three types, since it's each
    # run's sole control. Merging on target would collapse or
    # cross-attribute the three types, so assign control_field directly
    # from that type's own controls.csv instead of joining.
    gq_configs = {
        "gq_col": "configs_gq_col",
        "gq_mil": "configs_gq_mil",
        "gq_oth": "configs_gq_oth",
    }
    for name, config_dir in gq_configs.items():
        summary_path = f"./output/{run_folder}/final_summary_mgra_{name}.csv"
        if not os.path.exists(summary_path):
            continue

        gq_controls = pd.read_csv(f"./populationsim/{config_dir}/controls.csv")
        control_field = gq_controls.iloc[0]["control_field"]  # e.g. GQ_Military

        melted = _melt_summary(pd.read_csv(summary_path))
        melted["control_id"] = next_id
        melted["control_field"] = control_field
        next_id += 1
        all_rows.append(melted[["control_id", "control_field", "geography", "id", "control_value", "result"]])

    # Combine all control totals
    control_totals = pd.concat(all_rows, ignore_index=True)
    
    # Group and aggregate (replicating SQL GROUP BY and SUM)
    result = control_totals.groupby(
        ["control_id", "control_field", "geography", "id"], dropna=False
    ).agg(
        control_value=("control_value", "sum"),
        result=("result", "sum")
    ).reset_index()
    
    # Calculate differences
    result["Diff"] = result["result"] - result["control_value"]
    result["Diff %"] = result.apply(
        lambda row: 0 if row["result"] == row["control_value"]
        else None if row["control_value"] == 0
        else round(100.0 * (row["result"] - row["control_value"]) / row["control_value"], 2),
        axis=1
    )
    
    # Add Category column (replicating CASE statement)
    def categorize_control(control_field):
        """
        Categorizes a control field string into a broader category.

        Args:
            control_field (str): The control field to categorize.

        Returns:
            str or None: The category name if matched, otherwise None.
        """
        if control_field == "Total_HH":
            return "Households"
        elif control_field.startswith("HHSize_"):
            return "Household Size"
        elif control_field.startswith("HHInc_"):
            return "Household Income"
        elif control_field.startswith("HHWork_"):
            return "Household Workers"
        elif control_field in ["Male", "Female"]:
            return "Sex"
        elif control_field.startswith("Age_"):
            return "Age"
        elif control_field in ["Asian", "Black", "Hispanic", "Other", "Two_or_more", "White"]:
            return "Race/Ethnicity"
        elif control_field.startswith("job_"):
            return "Labor Force"
        elif control_field.startswith("lfp_"):
            return "Civilian Labor Force"
        elif control_field == "Total_GQ" or control_field.startswith("GQ_"):
            return "Group Quarters"
        return None
    
    result["Category"] = result["control_field"].apply(categorize_control)
    
    # Rename columns to match database output
    result = result.rename(columns={
        "control_id": "id",
        "control_field": "Control Field",
        "id": "geography_id",
        "control_value": "Control",
        "result": "Result"
    })
    
    # Select and order columns to match database output
    result = result[[
        "id", "Category", "Control Field", "geography", "geography_id",
        "Control", "Result", "Diff", "Diff %"
    ]]
    
    # Sort like the SQL query
    result = result.sort_values(
        by=["id", "Control Field", "geography", "geography_id"]
    ).reset_index(drop=True)
    
    return result


@st.cache_data
def summarize_controls(df: pd.DataFrame) -> pd.DataFrame:
    """Compute summary statistics for Controls."""
    result = pd.DataFrame()
    for field in ["Control Field", "Category"]:
        summary = (
            df.groupby(field)
            .agg(
                id=("id", "min"),
                Avg_Diff=("Diff", "mean"),
                Med_Diff=("Diff", "median"),
                Avg_Diff_Pct=("Diff %", "mean"),
                Med_Diff_Pct=("Diff %", "median"),
                Max_Diff=("Diff", lambda x: x.abs().max()),
                Max_Diff_Pct=("Diff %", lambda x: x.abs().max()),
            )
            .round(2)
            .reset_index()
            .set_index("id")
            .sort_index()
            .rename(
                columns={
                    field: "Control Field",
                    "Avg_Diff": "Avg Diff",
                    "Med_Diff": "Med Diff",
                    "Avg_Diff_Pct": "Avg Diff %",
                    "Med_Diff_Pct": "Med Diff %",
                    "Max_Diff": "Max |Diff|",
                    "Max_Diff_Pct": "Max |Diff %|",
                }
            )
        )

        result = pd.concat([result, summary])

    return result


# Get SQL engine
engine = get_engine()


# Load run metadata
run_df = get_run_metadata(_sql_engine=engine)
local_run_df = get_local_run_metadata()


# --- Source Toggle ---
source_options = ["Database"]
if not local_run_df.empty:
    source_options.append("Local Output")
source_choice = st.sidebar.radio("Choose data source:", source_options, index=0)

# --- Show only the relevant table and selection ---
selection = None
source_type = None

if source_choice == "Database":
    st.sidebar.markdown("### 📊 Database Runs")
    st.sidebar.markdown("Select a PopulationSim run to view validation results.")
    db_selection = st.sidebar.dataframe(
        data=run_df[["run_id", "staging_schema", "year", "date", "user", "version"]],
        hide_index=True,
        column_config={"year": st.column_config.TextColumn("year", max_chars=4)},
        on_select="rerun",
        selection_mode="single-row",
        key="db_runs"
    )
    if db_selection["selection"]["rows"]:
        selection = db_selection
        source_type = "database"
elif source_choice == "Local Output":
    st.sidebar.markdown("### 📁 Local Output Runs")
    local_selection = st.sidebar.dataframe(
        data=local_run_df[["run_id", "folder", "year", "date", "version"]],
        hide_index=True,
        column_config={"year": st.column_config.TextColumn("year", max_chars=4)},
        on_select="rerun",
        selection_mode="single-row",
        key="local_runs"
    )
    if local_selection["selection"]["rows"]:
        selection = local_selection
        source_type = "local"

# Set the user selection if provided
if selection and selection["selection"]["rows"]:
    idx = selection["selection"]["rows"][0]
    
    # Get run details based on source type
    if source_type == "database":
        run_id = run_df.iloc[idx]["run_id"]
        comments = run_df.iloc[idx]["comments"]
        controls_df = get_control_data(run_id=run_id, _sql_engine=engine)
        # Normalize geography to lowercase for consistency
        controls_df["geography"] = controls_df["geography"].str.lower()
    else:
        run_id = local_run_df.iloc[idx]["run_id"]
        run_folder = local_run_df.iloc[idx]["folder"]
        comments = f"Local run from output/{run_folder}/"
        controls_df = get_control_data_from_local(run_folder=run_folder)

    # Display report title and run selected
    st.markdown("<h1>PopulationSim Validation</h1>", unsafe_allow_html=True)
    st.markdown(f"## [run_id] = {run_id}")
    st.markdown("Comments: " + comments)

    # Setting up tabs
    tab1, tab2, tab3 = st.tabs(["Region", "PUMA", "MGRA"])

    # Region section
    with tab1:
        st.markdown("### Region Controls")

        # Numeric Difference Plot
        st.plotly_chart(
            build_scatter_plot(
                df=controls_df[controls_df["geography"] == "region"],
                y_var="Diff",
                hover_data="Control Field",
                title="Region Controls - Numeric Difference",
            )
        )

        # Percent Difference Plot
        st.plotly_chart(
            build_scatter_plot(
                df=controls_df[controls_df["geography"] == "region"],
                y_var="Diff %",
                hover_data="Control Field",
                title="Region Controls - Percent Difference",
            )
        )

        # Summary table
        st.write(f"**Summary Table for Region Controls**")
        st.dataframe(
            controls_df[controls_df["geography"] == "region"][
                [
                    "Category",
                    "Control Field",
                    "Control",
                    "Result",
                    "Diff",
                    "Diff %",
                ]
            ],
            hide_index=True,
        )

    # PUMA Section
    with tab2:
        st.markdown("### PUMA Controls")

        # Allow user to select unique control category
        category = st.selectbox(
            "Pick a category to analyze",
            controls_df[controls_df["geography"] == "puma"]["Category"].unique(),
        )

        # For the selected category
        st.markdown(f"#### {category}")
        tbl = controls_df.query("geography == 'puma' & Category == @category")[
            [
                "id",
                "Category",
                "geography_id",
                "Control Field",
                "Control",
                "Result",
                "Diff",
                "Diff %",
            ]
        ]

        # Numeric Difference Plot
        st.plotly_chart(
            build_scatter_plot(
                df=tbl,
                y_var="Diff",
                hover_data="geography_id",
                title=f"{category} - Numeric Difference",
            )
        )

        # Percent Difference Plot
        st.plotly_chart(
            build_scatter_plot(
                df=tbl,
                y_var="Diff %",
                hover_data="geography_id",
                title=f"{category} - Percent Difference",
            )
        )

        # Summary table
        st.write(f"**Summary Statistics for {category}**")
        summary = summarize_controls(tbl)
        summary_html = summary.to_html(
            index=False,
            formatters={
                "Avg Diff": lambda x: f"{x:,.0f}",
                "Med Diff": lambda x: f"{x:,.0f}",
                "Avg Diff %": lambda x: f"{x:,.0f}",
                "Med Diff %": lambda x: f"{x:,.0f}",
                "Max |Diff|": lambda x: f"{x:,.0f}",
                "Max |Diff %|": lambda x: f"{x:,.0f}",
            },
        )

        st.markdown(summary_html, unsafe_allow_html=True)

    # MGRA Section
    with tab3:

        st.markdown("### MGRA Controls")

        # Allow user to select unique control category
        category = st.selectbox(
            "Pick a category to analyze",
            controls_df[controls_df["geography"] == "mgra"]["Category"].unique(),
        )

        # For the selected category
        st.markdown(f"#### {category}")
        tbl = controls_df.query("geography == 'mgra' & Category == @category")[
            [
                "id",
                "Category",
                "geography_id",
                "Control Field",
                "Control",
                "Result",
                "Diff",
                "Diff %",
            ]
        ]

        # Numeric Difference Plot
        st.plotly_chart(
            build_scatter_plot(
                df=tbl,
                y_var="Diff",
                hover_data="geography_id",
                title=f"{category} - Numeric Difference",
            )
        )

        # Percent Difference Plot
        st.plotly_chart(
            build_scatter_plot(
                df=tbl,
                y_var="Diff %",
                hover_data="geography_id",
                title=f"{category} - Percent Difference",
            )
        )

        # Summary table
        st.write(f"**Summary Statistics for {category}**")
        summary = summarize_controls(tbl)
        summary_html = summary.to_html(
            index=False,
            formatters={
                "Avg Diff": lambda x: f"{x:,.0f}",
                "Med Diff": lambda x: f"{x:,.0f}",
                "Avg Diff %": lambda x: f"{x:,.0f}",
                "Med Diff %": lambda x: f"{x:,.0f}",
                "Max |Diff|": lambda x: f"{x:,.0f}",
                "Max |Diff %|": lambda x: f"{x:,.0f}",
            },
        )

        st.markdown(summary_html, unsafe_allow_html=True)
