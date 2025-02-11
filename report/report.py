import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from IPython.display import display
import yaml
import streamlit as st
import sqlalchemy as sql


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
controls_df = get_control_data(run_id=run_id, _sql_engine=engine)

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
        controls_df[controls_df["geography"] == "PUMA"]["Category"].unique(),
    )

    # For the selected category
    st.markdown(f"#### {category}")
    tbl = controls_df.query("geography == 'PUMA' & Category == @category")[
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
