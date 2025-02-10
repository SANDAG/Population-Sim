import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from IPython.display import display
import yaml
import streamlit as st
import sqlalchemy as sql


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


def summarize_controls(df: pd.DataFrame) -> pd.DataFrame:
    """Compute summary statistics for Controls."""
    result = pd.DataFrame()
    for field in ["Control Field", "Category"]:
        summary = (
            df.groupby(field)
            .agg(
                Avg_Diff=("Diff", "mean"),
                Med_Diff=("Diff", "median"),
                Avg_Diff_Pct=("Diff %", "mean"),
                Med_Diff_Pct=("Diff %", "median"),
                Max_Diff=("Diff", lambda x: x.abs().max()),
                Max_Diff_Pct=("Diff %", lambda x: x.abs().max()),
            )
            .round(2)
            .reset_index()
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
with engine.connect() as connection:
    with open("./report/metadata.sql", "r") as query:
        run_df = pd.read_sql_query(
            sql.text(query.read()),
            connection,
        )

# Set a default run_id and associated comments
run_id = run_df["run_id"].min()
comments = run_df[run_df["run_id"] == run_id]["comments"].values[0]

# Allow user to select a single run from the metadata table
st.sidebar.markdown("Select a PopulationSim run to view validation results.")
selection = st.sidebar.dataframe(
    data=run_df[["run_id", "staging_schema", "year", "date", "user", "version"]],
    hide_index=True,
    column_config={"year": st.column_config.TextColumn("year", max_chars=4)},
    on_select="rerun",
    selection_mode="single-row",
)

# Set the user selection if provided
if not selection["selection"]["rows"]:
    pass  # Empty list implies no selection made
else:
    idx = selection["selection"]["rows"][0]
    run_id = run_df.iloc[idx]["run_id"]
    comments = run_df.iloc[idx]["comments"]

# Load control values and results for selected run
with engine.connect() as connection:
    with open("./report/controls.sql", "r") as query:
        controls_df = pd.read_sql_query(
            sql.text(query.read().format(run_id=run_id)),
            connection,
        )

# Display report title and run selected
st.markdown("<h1>PopulationSim Validation</h1>", unsafe_allow_html=True)
st.markdown(f"## [run_id] = {run_id}")
st.markdown("Comments: " + comments)

# Setting up tabs
tab1, tab2, tab3 = st.tabs(["Region", "PUMA", "MGRA"])

# Region section
with tab1:

    st.markdown("### Region")

    # Numeric Difference Plot
    st.plotly_chart(
        build_scatter_plot(
            df=controls_df[controls_df["geography"] == "region"],
            y_var="Diff",
            hover_data="Control Field",
            title="Control Matching - Numeric Difference",
        )
    )

    # Percent Difference Plot
    st.plotly_chart(
        build_scatter_plot(
            df=controls_df[controls_df["geography"] == "region"],
            y_var="Diff %",
            hover_data="Control Field",
            title="Control Matching - Percent Difference",
        )
    )

    # Summary Table for Region
    show_fields = [
        "id",
        "Category",
        "Control Field",
        "Control",
        "Result",
        "Diff",
        "Diff %",
    ]
    region_controls_df = controls_df[controls_df["geography"] == "region"][
        show_fields
    ].copy()

    st.write("Regional Control values")
    st.dataframe(region_controls_df, hide_index=True)


# PUMA Section
with tab2:

    st.markdown("### PUMA")

    # puma_df
    puma_df = controls_df[controls_df["geography"] == "PUMA"]
    # For each category
    categories = puma_df["Category"].unique()
    # Chosse a category
    category = st.selectbox(
        "Pick a category to analyze", categories, key="puma_category"
    )
    st.markdown(f"#### {category}")
    control_cols = [
        "Category",
        "geography_id",
        "Control Field",
        "Control",
        "Result",
        "Diff",
        "Diff %",
    ]
    tbl = puma_df.query("Category == @category")[control_cols]

    # Numeric Difference Plot for PUMA
    st.plotly_chart(
        build_scatter_plot(
            df=tbl,
            y_var="Diff",
            hover_data="geography_id",
            title=f"{category} - Numeric Difference",
        )
    )

    # Percent Difference Plot for PUMA
    st.plotly_chart(
        build_scatter_plot(
            df=tbl,
            y_var="Diff %",
            hover_data="geography_id",
            title=f"{category} - Percent Difference",
        )
    )

    # Summary table
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

    st.markdown("### MGRA")

    # mgra df
    mgra_df = controls_df[controls_df["geography"] == "mgra"]

    # For each Category of MGRA controls
    categories = mgra_df["Category"].unique()

    # Chosse a category
    category = st.selectbox(
        "Pick a category to analyze", categories, key="mgra_category"
    )

    control_cols = [
        "Category",
        "geography_id",
        "Control Field",
        "Control",
        "Result",
        "Diff",
        "Diff %",
    ]
    tbl = mgra_df.query("Category == @category")[control_cols]

    st.markdown(f"#### {category}")

    # Numeric Difference Plot for MGRA
    st.plotly_chart(
        build_scatter_plot(
            df=tbl,
            y_var="Diff",
            hover_data="geography_id",
            title=f"{category} - Numeric Difference",
        )
    )

    # Percent Difference Plot for MGRA
    st.plotly_chart(
        build_scatter_plot(
            df=tbl,
            y_var="Diff %",
            hover_data="geography_id",
            title=f"{category} - Percent Difference",
        )
    )

    # Summary table
    st.write(f"Summary Statistics for {category}")
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
