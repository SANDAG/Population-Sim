import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from IPython.display import display, HTML
import yaml
import streamlit as st
import sqlalchemy as sql
import sys


def build_scatter_plot(df, y_var, title, x_range=None, y_range=None) -> None:
    """Build Control Scatter plot for a given control."""
    plt.figure(figsize=(8, 6))
    scatter = plt.scatter(df["Control"], df[y_var], s=75)
    plt.title(title)
    plt.xlabel("Control")
    plt.ylabel(y_var)

    # Add horizontal line at y=0
    plt.axhline(0, color="black", linewidth=1, linestyle="dashed")

    # Update x-axis and y-axis with provided ranges
    if x_range is not None:
        plt.xlim(x_range)
    if y_range is not None:
        plt.ylim(y_range)

    plt.show()


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

# run_id to be used in creating reports
run_id = int(sys.argv[1])
with open("./secrets.yml", "r") as file:
    secrets = yaml.safe_load(file)

# Build SQL engine from configuration
engine = sql.create_engine(
    "mssql+pyodbc://@"
    + secrets["sql"]["server"]
    + "/"
    + secrets["sql"]["output_database"]
    + "?trusted_connection=yes&driver=ODBC Driver 17 for SQL Server",
    fast_executemany=True,
)


# Load run metadata and controls/results from SQL
with engine.connect() as connection:
    with open("./report/metadata.sql", "r") as query:
        run_df = pd.read_sql_query(
            sql.text(query.read().format(run_id=run_id)),
            connection,
        )

    with open("./report/controls.sql", "r") as query:
        controls_df = pd.read_sql_query(
            sql.text(query.read().format(run_id=run_id)),
            connection,
        )

# Display run_id and explanatory text
st.markdown("<h1>PopulationSim Validation</h1>", unsafe_allow_html=True)
st.markdown(f"## [run_id] = {run_id}")
st.markdown("""
This report evaluates the alignment of PopulationSim outputs to controls for a given run. Run information is shown below.
""")
run_df = run_df.astype('str')
st.dataframe(run_df[["run_id", "staging_schema", "year", "date", "user", "version"]], hide_index=True)


# Setting up tabs
tab1, tab2, tab3 = st.tabs(["Region", "PUMA", "MGRA"])

# Region section 
with tab1:
    
    st.markdown("### Region")

    # Numeric Difference Plot
    fig = px.scatter(
        controls_df[controls_df["geography"] == "region"],
        x="Control",
        y="Diff",
        hover_data=["Control Field"],
        title="Control Matching - Numeric Difference",
    )
    fig.update_traces(marker=dict(size=12))
    fig.add_hline(y=0, line_dash="dash", line_color="black")
    st.plotly_chart(fig)

    # Percent Difference Plot
    fig = px.scatter(
        controls_df[controls_df["geography"] == "region"],
        x="Control",
        y="Diff %",
        hover_data=["Control Field"],
        title="Control Matching - Percent Difference",
    )
    fig.update_traces(marker=dict(size=12))
    fig.add_hline(y=0, line_dash="dash", line_color="black")
    st.plotly_chart(fig)

    # Summary Table for Region
    show_fields = ["id", "Category", "Control Field", "Control", "Result", "Diff", "Diff %"]
    region_controls_df = controls_df[controls_df["geography"] == "region"][show_fields].copy()

    st.write("Regional Control values")
    st.dataframe(region_controls_df, hide_index=True)


# PUMA Section
with tab2:
   
    st.markdown("### PUMA")

    #puma_df 
    puma_df = controls_df[controls_df["geography"] == "PUMA"]
     # For each category 
    categories = puma_df["Category"].unique()
    # Chosse a category
    category = st.selectbox("Pick a category to analyze", categories, key="puma_category")
    st.markdown(f"#### {category}")
    control_cols = ["Category", "geography_id", "Control Field", "Control", "Result", "Diff", "Diff %"]
    tbl = puma_df.query('Category == @category')[control_cols]
    
    # Numeric Difference Plot for PUMA
    fig = px.scatter(
        tbl,
        x="Control",
        y="Diff",
        color="Control Field",
        hover_data=["geography_id"],
        title=f"{category} - Numeric Difference",
    )
    fig.update_traces(marker=dict(size=12))
    fig.add_hline(y=0, line_dash="dash", line_color="black")
    st.plotly_chart(fig)
    
    # Percent Difference Plot for PUMA
    fig = px.scatter(
        tbl,
        x="Control",
        y="Diff %",
        color="Control Field",
        hover_data=["geography_id"],
        title=f"{category} - Percent Difference",
    )
    fig.update_traces(marker=dict(size=12))
    fig.add_hline(y=0, line_dash="dash", line_color="black")
    st.plotly_chart(fig)
    
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
            }
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
    category = st.selectbox("Pick a category to analyze", categories, key="mgra_category")

   
    control_cols = ["Category", "geography_id", "Control Field", "Control", "Result", "Diff", "Diff %"]
    tbl = mgra_df.query('Category == @category')[control_cols]

    
    st.markdown(f"#### {category}")

    # Numeric Difference Plot for MGRA
    fig = px.scatter(
        tbl,
        x="Control",
        y="Diff",
        color="Control Field",
        hover_data=["geography_id"],
        title=f"{category} - Numeric Difference",
    )
    fig.update_traces(marker=dict(size=12))
    fig.add_hline(y=0, line_dash="dash", line_color="black")
    st.plotly_chart(fig)

    # Percent Difference Plot for MGRA
    fig = px.scatter(
        tbl,
        x="Control",
        y="Diff %",
        color="Control Field",
        hover_data=["geography_id"],
        title=f"{category} - Percent Difference",
    )
    fig.update_traces(marker=dict(size=12))
    fig.add_hline(y=0, line_dash="dash", line_color="black")
    st.plotly_chart(fig)

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
        }
    )

    st.markdown(summary_html, unsafe_allow_html=True)
