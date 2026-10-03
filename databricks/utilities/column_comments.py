"""Column types and comments for the silver seed and synthetic population tables.

Uppercase names are ACS PUMS variables; their full code lists are in the
Census "ACS PUMS Data Dictionary 2017-2021". Lowercase names are either derived
in sql/seed_*.sql / python/build_seed_data.py or renamed in the silver layer.

Comments are applied through the table's declared schema (@dp.table(schema=
schema_ddl(...))). The pipeline ignores comments attached as DataFrame column
metadata, so the schema is the only place they stick. The declared schema must
list every column the table function returns, with matching types: when a
source CSV gains or loses a column, update the *_TYPES list here too.
"""


def schema_ddl(types: list, comments: dict) -> str:
    """DDL schema string for @dp.table(schema=...): every (column, type) pair in
    types, in order, with a COMMENT wherever comments has an entry."""
    def _column(name, type_):
        ddl = f"`{name}` {type_}"
        if name in comments:
            escaped = comments[name].replace("\\", "\\\\").replace("'", "\\'")
            ddl += f" COMMENT '{escaped}'"
        return ddl

    return ",\n".join(_column(name, type_) for name, type_ in types)


# Columns added by the exporter / silver layer to every table
_RUN_COLUMNS = {
    "run_id": "Pipeline run identifier, assigned once per (run_timestamp, year) in run_id_lookup",
    "year": "Model year of the PopSim run (output folder name)",
    "run_timestamp": "Timestamp of the PopSim export this row came from",
}

# --- Household-level PUMS variables (keyed by raw name) ---
_HH = {
    "SERIALNO": "PUMS housing unit / GQ serial number; first 4 characters are the ACS survey year",
    "PUMA": "Public Use Microdata Area (2010 PUMA definitions in the 2017-2021 ACS PUMS)",
    "NP": "Number of persons in the housing unit (1 for group quarters records)",
    "HINCP": "Household income, past 12 months, in survey-year dollars (PUMS HINCP, not ADJINC-adjusted)",
    "HHADJINC": "Household income adjusted to 2022 dollars with the San Diego CPI by survey year; GQ records use person income (PINCP)",
    "HHT": "Household/family type: 1 married couple; 2 other family, male householder no spouse; 3 other family, female householder no spouse; 4 nonfamily male living alone; 5 nonfamily male not alone; 6 nonfamily female living alone; 7 nonfamily female not alone",
    "HUPAC": "Presence and age of children: 1 under 6 only; 2 aged 6-17 only; 3 both under 6 and 6-17; 4 no children",
    "VEH": "Vehicles available: 0-5, 6 = 6 or more",
    "BLD": "Units in structure: 1 mobile home/trailer; 2 one-family detached; 3 one-family attached; 4 2 apartments; 5 3-4; 6 5-9; 7 10-19; 8 20-49; 9 50+; 10 boat/RV/van",
    "TYPEHUGQ": "Record type: 1 housing unit; 2 institutional group quarters; 3 noninstitutional group quarters",
    "gq_type": "Derived: 0 housing unit; 1 military GQ; 2 college GQ; 3 other GQ",
    "workers": "Derived: number of persons in the unit with ESR in (1,2,4,5), i.e. employed civilians or armed forces",
    "WGTP": "Seed weight: PUMS housing unit weight (WGTP) for housing units, person weight (PWGTP) for GQ records",
}

# --- Person-level PUMS variables (keyed by raw name) ---
_PERSON = {
    "SERIALNO": _HH["SERIALNO"],
    "PUMA": _HH["PUMA"],
    "SPORDER": "Person number within the housing unit (1 = householder)",
    "AGEP": "Age in years (top-coded)",
    "SEX": "Sex: 1 male; 2 female",
    "ESR": "Employment status recode: 1 civilian employed, at work; 2 civilian employed, with a job but not at work; 3 unemployed; 4 armed forces, at work; 5 armed forces, with a job but not at work; 6 not in labor force; N/A for under 16",
    "COW": "Class of worker: 1 private for-profit; 2 private not-for-profit; 3 local government; 4 state government; 5 federal government; 6 self-employed, not incorporated; 7 self-employed, incorporated; 8 unpaid family worker; 9 unemployed, last worked 5+ years ago or never worked",
    "WKHP": "Usual hours worked per week, past 12 months (99 = 99 or more)",
    "WKW": "Weeks worked, past 12 months (PUMS WKW; coding changed in the 2019 ACS, see the data dictionary)",
    "SCHG": "Grade level attending: 1 nursery/preschool; 2 kindergarten; 3-14 grades 1-12; 15 college undergraduate; 16 graduate/professional school; 0 = not attending",
    "SCHL": "Educational attainment: 1 no schooling ... 16 regular high school diploma; 17 GED; 18-19 some college; 20 associate's; 21 bachelor's; 22 master's; 23 professional degree; 24 doctorate",
    "HISP": "Hispanic origin: 1 not Spanish/Hispanic/Latino; 2-24 specific Hispanic origin groups",
    "RAC1P": "Race: 1 White alone; 2 Black alone; 3 American Indian alone; 4 Alaska Native alone; 5 American Indian and Alaska Native, not specified; 6 Asian alone; 7 Native Hawaiian/Pacific Islander alone; 8 some other race alone; 9 two or more races",
    "MIL": "Military service: 1 now on active duty; 2 active duty in the past, not now; 3 Reserves/National Guard training only; 4 never served; N/A for under 17",
    "OCCP": "Census occupation code",
    "SOCP": "SOC-based occupation code",
    "SOC2": "Derived: first 2 characters of SOCP (SOC major occupation group)",
    "NAICSP": "NAICS-based industry code",
    "NAICS2": "Derived: 2-digit NAICS sector, except 'MIL' for military (NAICSP 9281*) and 3 digits for sector 72 (721 accommodation, 722 food services); drives the job_* controls",
    "TYPEHUGQ": _HH["TYPEHUGQ"],
    "gq_type": _HH["gq_type"],
    "PINCP": "Total person income, past 12 months, in survey-year dollars (not ADJINC-adjusted)",
}


def _renamed(base: dict, renames: dict) -> dict:
    """Re-key base comments from raw PUMS names to silver column names."""
    return {renames.get(k, k): v for k, v in base.items()}


# Renames applied in silver_synthetic_households / silver_synthetic_persons
SYNTHETIC_HOUSEHOLD_RENAMES = {
    "SERIALNO": "serialno",
    "NP": "num_persons",
    "HHADJINC": "hh_adj_income",
    "HHT": "hh_type",
    "HUPAC": "presence_of_children",
    "VEH": "vehicles",
    "BLD": "building_type",
}

SYNTHETIC_PERSON_RENAMES = {
    "SERIALNO": "serialno",
    "SPORDER": "person_order",
    "AGEP": "age",
    "ESR": "employment_status",
    "COW": "class_of_worker",
    "WKHP": "work_hours_per_week",
    "SCHG": "school_grade",
    "RAC1P": "race",
    "HISP": "hispanic_origin",
    "MIL": "military_service",
    "SCHL": "education_attainment",
    "OCCP": "occupation_code",
    "WKW": "weeks_worked",
    "NAICSP": "naics_industry_code",
    "NAICS2": "naics_2digit",
    "SOCP": "soc_occupation_code",
    "SOC2": "soc_2digit",
    "SEX": "sex",
}

_SYNTHETIC_COMMON = {
    "household_id": "Synthetic household identifier, unique within a run across the household and GQ syntheses",
    "mgra": "MGRA (Master Geographic Reference Area) the synthetic household is allocated to",
}

# In the synthetic output, N/A values in these columns were filled with 0
# by python/outputs.py before export.
_ZERO_IS_NA = "; 0 = N/A (filled before export)"

_SYNTHESIS_RUN = "Synthesis run whose seed file this row came from: household, gq_mil, gq_col or gq_oth"

SEED_HOUSEHOLDS = {
    **_RUN_COLUMNS,
    **_HH,
    "hhid": "Seed household id: sequential by SERIALNO within each seed file, so not unique across the unioned household and GQ seeds",
    "synthesis_run": _SYNTHESIS_RUN,
}

SEED_PERSONS = {
    **_RUN_COLUMNS,
    **_PERSON,
    "laborforce": "Derived: 1 if ESR in (1-5), i.e. in the labor force (civilian or armed forces), else 0",
    "worker": "Derived: 1 if ESR in (1,2,4,5), i.e. employed (civilian or armed forces), else 0",
    "race": "Derived race/ethnicity control category: Hispanic (any race), White alone, Black or African American alone, Asian alone, Two or More Races, Other",
    "hhid": "Seed household id linking to silver_seed_households.hhid within the same seed file",
    "synthesis_run": _SYNTHESIS_RUN,
}

SYNTHETIC_HOUSEHOLDS = {
    **_RUN_COLUMNS,
    **_SYNTHETIC_COMMON,
    **_renamed({
        **_HH,
        "HHADJINC": _HH["HHADJINC"] + "; negative values clipped to 0",
        "HHT": _HH["HHT"] + _ZERO_IS_NA,
        "HUPAC": _HH["HUPAC"] + _ZERO_IS_NA,
        "BLD": _HH["BLD"] + _ZERO_IS_NA,
    }, SYNTHETIC_HOUSEHOLD_RENAMES),
}

SYNTHETIC_PERSONS = {
    **_RUN_COLUMNS,
    **_SYNTHETIC_COMMON,
    **_renamed({
        **_PERSON,
        **{k: _PERSON[k] + _ZERO_IS_NA
           for k in ("ESR", "COW", "WKHP", "MIL", "SCHL", "OCCP", "WKW")},
    }, SYNTHETIC_PERSON_RENAMES),
}


# --- Declared column types, in table column order ---
# Seed PUMS columns that are integers with nulls arrive from the parquet as
# DOUBLE; the silver seed tables cast them to INT, so they are INT here.

_RUN_ID = [("run_id", "BIGINT"), ("year", "INT")]
_RUN_TIMESTAMP = [("run_timestamp", "TIMESTAMP_NTZ")]

SEED_HOUSEHOLD_TYPES = _RUN_ID + [
    ("SERIALNO", "STRING"),
    ("PUMA", "BIGINT"),
    ("NP", "INT"),
    ("HINCP", "INT"),
    ("HHADJINC", "INT"),
    ("HHT", "INT"),
    ("workers", "BIGINT"),
    ("HUPAC", "INT"),
    ("VEH", "INT"),
    ("BLD", "INT"),
    ("TYPEHUGQ", "BIGINT"),
    ("gq_type", "BIGINT"),
    ("WGTP", "DOUBLE"),  # a weight, so left uncast even though current values are whole
    ("hhid", "BIGINT"),
    ("synthesis_run", "STRING"),
] + _RUN_TIMESTAMP

SEED_PERSON_TYPES = _RUN_ID + [
    ("SERIALNO", "STRING"),
    ("SPORDER", "INT"),
    ("PUMA", "BIGINT"),
    ("AGEP", "INT"),
    ("SEX", "BIGINT"),
    ("ESR", "INT"),
    ("laborforce", "BIGINT"),
    ("worker", "BIGINT"),
    ("COW", "INT"),
    ("WKHP", "INT"),
    ("SCHG", "BIGINT"),
    ("HISP", "BIGINT"),
    ("RAC1P", "BIGINT"),
    ("race", "STRING"),
    ("MIL", "INT"),
    ("SCHL", "INT"),
    ("OCCP", "INT"),
    ("WKW", "INT"),
    ("NAICSP", "STRING"),
    ("NAICS2", "STRING"),
    ("SOCP", "STRING"),
    ("SOC2", "INT"),
    ("TYPEHUGQ", "BIGINT"),
    ("gq_type", "BIGINT"),
    ("PINCP", "INT"),
    ("hhid", "BIGINT"),
    ("synthesis_run", "STRING"),
] + _RUN_TIMESTAMP

SYNTHETIC_HOUSEHOLD_TYPES = _RUN_ID + [
    ("household_id", "BIGINT"),
    ("mgra", "BIGINT"),
    ("serialno", "STRING"),
    ("num_persons", "INT"),
    ("hh_adj_income", "INT"),
    ("hh_type", "INT"),
    ("presence_of_children", "INT"),
    ("vehicles", "INT"),
    ("building_type", "INT"),
    ("gq_type", "BIGINT"),
    ("workers", "BIGINT"),
] + _RUN_TIMESTAMP

SYNTHETIC_PERSON_TYPES = _RUN_ID + [
    ("mgra", "BIGINT"),
    ("household_id", "BIGINT"),
    ("serialno", "STRING"),
    ("person_order", "INT"),
    ("age", "INT"),
    ("sex", "BIGINT"),
    ("employment_status", "INT"),
    ("class_of_worker", "INT"),
    ("work_hours_per_week", "INT"),
    ("school_grade", "BIGINT"),
    ("race", "BIGINT"),
    ("hispanic_origin", "BIGINT"),
    ("military_service", "INT"),
    ("education_attainment", "INT"),
    ("occupation_code", "INT"),
    ("weeks_worked", "INT"),
    ("naics_industry_code", "STRING"),
    ("naics_2digit", "STRING"),
    ("soc_occupation_code", "STRING"),
    ("soc_2digit", "INT"),
] + _RUN_TIMESTAMP
