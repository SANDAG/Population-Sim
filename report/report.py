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
    """Scan output directory for local runs and build metadata DataFrame."""
    local_runs = []
    
    if not os.path.exists(output_dir):
        return pd.DataFrame(columns=["run_id", "year", "date", "version", "source"])
    
    # Scan output directory for year folders
    for folder in sorted(os.listdir(output_dir)):
        folder_path = os.path.join(output_dir, folder)
        
        if not os.path.isdir(folder_path):
            continue
        
        # Check for required files
        timing_log = os.path.join(folder_path, "timing_log.csv")
        synthetic_hh = os.path.join(folder_path, f"synthetic_households_{folder}.csv")
        synthetic_persons = os.path.join(folder_path, f"synthetic_persons_{folder}.csv")
        
        # Only include if all required files exist
        if all(os.path.exists(f) for f in [timing_log, synthetic_hh, synthetic_persons]):
            # Get modification time from timing_log
            mod_time = datetime.fromtimestamp(os.path.getmtime(timing_log))
            
            local_runs.append({
                "run_id": f"{folder}_local",
                "year": folder,
                "date": mod_time.strftime("%Y-%m-%d %H:%M"),
                "version": "local",
                "source": "local"
            })
    
    return pd.DataFrame(local_runs)


@st.cache_data
def get_control_data_from_local(year: str) -> pd.DataFrame:
    """Load control data from local CSV files and replicate database query logic."""
    
    # Load controls definition
    controls_df = pd.read_csv("./populationsim/configs/controls.csv")
    
    # Add GQ controls from settings (mirrors etl_controls_csv behavior)
    settings_file = "populationsim/configs/settings.yaml"
    with open(settings_file, "r") as file:
        settings = yaml.safe_load(file)
    
    # Get GQ control columns and expressions and append to controls DataFrame
    for item in settings["gq_options"]["GQ_control_map"]:
        result = {
            "target": item["control_column"],
            "geography": "mgra",
            "seed_table": "persons",
            "importance": None,
            "control_field": item["control_column"],
            "expression": settings["gq_options"]["GQ_type_column"] + " == " + str(item["code"]),
        }
        df_gq = pd.Series(result).to_frame().T
        controls_df = pd.concat([controls_df, df_gq], ignore_index=True)
    
    controls_df["control_id"] = range(1, len(controls_df) + 1)
    
    # Load summary files
    summary_files = {
        "mgra": f"./output/{year}/final_summary_mgra.csv",
        "mgra_gq": f"./output/{year}/final_summary_mgra_gq.csv",
        "PUMA": f"./output/{year}/final_summary_mgra_PUMA.csv",
        "region": f"./output/{year}/final_summary_region_1.csv",
    }
    
    all_control_totals = []
    
    # Process MGRA summaries
    for key in ["mgra", "mgra_gq", "PUMA"]:
        if os.path.exists(summary_files[key]):
            df = pd.read_csv(summary_files[key])
            control_cols = [col for col in df.columns if col.endswith("_control")]
            result_cols = [col for col in df.columns if col.endswith("_result")]
            
            df_control = df.melt(
                id_vars=["geography", "id"],
                value_vars=control_cols,
                var_name="target",
                value_name="control_value",
            )
            df_result = df.melt(
                id_vars=["geography", "id"],
                value_vars=result_cols,
                var_name="target",
                value_name="result",
            )
            
            df_control["target"] = df_control["target"].str.replace("_control", "")
            df_result["target"] = df_result["target"].str.replace("_result", "")
            
            merged = pd.merge(df_control, df_result, on=["geography", "id", "target"])
            # Normalize geography to lowercase for consistency
            merged["geography"] = merged["geography"].str.lower()
            all_control_totals.append(merged)
    
    # Process region summary
    if os.path.exists(summary_files["region"]):
        df = pd.read_csv(summary_files["region"])
        df = df[["control_name", "control_value", "mgra_integer_weight"]]
        df.insert(0, "geography", "region")
        df.insert(1, "id", 1)
        df.columns = ["geography", "id", "target", "control_value", "result"]
        all_control_totals.append(df)
    
    # Combine all control totals
    control_totals = pd.concat(all_control_totals, ignore_index=True)
    
    # Merge with controls definition
    control_totals = control_totals.merge(
        controls_df[["control_id", "target", "control_field"]],
        on="target",
        how="left"
    )
    
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
        if control_field == "Total_HH":
            return "Households"
        elif control_field.startswith("HHSize_"):
            return "Household Size"
        elif control_field.startswith("HHInc_"):
            return "Household Income"
        elif control_field.startswith("HHWork_"):
            return "Household Workers"
        elif control_field.startswith("HHChild_"):
            return "Household Children"
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
        elif control_field.startswith("gq_"):
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


# Build SQL engine from secrets file
with open("./secrets.yml", "r") as file:
    secrets = yaml.safe_load(file)

engine = sql.create_engine(
    "mssql+pyodbc://@"
    + secrets["sql"]["server"]
    + "/"
    + secrets["sql"]["output_database"]
    + "?trusted_connection=yes&driver=ODBC Driver 17 for SQL Server",
    fast_executemany=True,
)


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
        data=local_run_df[["run_id", "year", "date", "version"]],
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
        year = local_run_df.iloc[idx]["year"]
        comments = f"Local run from output/{year}/"
        controls_df = get_control_data_from_local(year=year)

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
