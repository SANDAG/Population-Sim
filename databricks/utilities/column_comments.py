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
    "run_id": "Pipeline run identifier, one per (run_timestamp, year) from run_id_lookup, numbered in ingestion order",
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
    "household_id": "hhid",
    "SERIALNO": "serialno",
    "NP": "persons",
    "HHADJINC": "hinc",
    "HHT": "hht",
    "workers": "num_workers",
    "HUPAC": "presence_of_children",
    "VEH": "veh",
    "BLD": "bldgsz",
}

SYNTHETIC_PERSON_RENAMES = {
    "household_id": "hhid",
    "SERIALNO": "serialno",
    "SPORDER": "pnum",
    "AGEP": "age",
    "ESR": "employment_status",
    "COW": "class_of_worker",
    "WKHP": "hours",
    "SCHG": "school_grade",
    "RAC1P": "rac1p",
    "HISP": "hispanic_origin",
    "MIL": "military_service",
    "SCHL": "education_attainment",
    "OCCP": "occupation_code",
    "WKW": "weeks",
    "NAICSP": "naics_industry_code",
    "NAICS2": "naics_2digit",
    "SOCP": "soc_occupation_code",
    "SOC2": "soc2",
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
    **_renamed(_SYNTHETIC_COMMON, SYNTHETIC_HOUSEHOLD_RENAMES),
    **_renamed({
        **_HH,
        "HHADJINC": _HH["HHADJINC"] + "; negative values clipped to 0",
        "HHT": _HH["HHT"] + _ZERO_IS_NA,
        "HUPAC": _HH["HUPAC"] + _ZERO_IS_NA,
        "BLD": _HH["BLD"] + _ZERO_IS_NA,
    }, SYNTHETIC_HOUSEHOLD_RENAMES),
    "hhid": _SYNTHETIC_COMMON["household_id"],
    "household_serial_no": "ABM household serial number placeholder; always 0",
    "taz": "Household TAZ from the MGRA-based input for the same synthesis run",
    "hinccat1": "ABM income category: 1 < $30k; 2 $30k-<$60k; 3 $60k-<$100k; 4 $100k-<$150k; 5 >= $150k",
    "hinc": _HH["HHADJINC"] + "; negative values clipped to 0; missing values filled with 0",
    "num_workers": _HH["workers"] + "; missing values filled with 0",
    "veh": _HH["VEH"] + "; missing values filled with 0",
    "unittype": "ABM unit type: gq_type 1, 2 and 3 mapped to 1; other values unchanged",
    "version": "ABM household version placeholder; always 0",
    "poverty": "Household income divided by the 2022 ASPE poverty guideline for household size; missing income remains null",
}

SYNTHETIC_PERSONS = {
    **_RUN_COLUMNS,
    **_renamed(_SYNTHETIC_COMMON, SYNTHETIC_PERSON_RENAMES),
    **_renamed({
        **_PERSON,
        **{k: _PERSON[k] + _ZERO_IS_NA
           for k in ("ESR", "COW", "WKHP", "MIL", "SCHL", "OCCP", "WKW")},
    }, SYNTHETIC_PERSON_RENAMES),
    "hhid": _SYNTHETIC_COMMON["household_id"],
    "perid": "ABM person identifier, sequential within each run ordered by hhid and pnum",
    "household_serial_no": "ABM household serial number placeholder; always 0",
    "miltary": "ABM military flag: 1 if military_service is 1, otherwise 0; source spelling retained",
    "pemploy": "ABM employment status: 1 full-time; 2 part-time; 3 not employed; 4 under age 16",
    "pstudent": "ABM student status: 1 grade/high school; 2 university; 3 not a student",
    "ptype": "ABM person type: 1 full-time worker; 2 part-time worker; 3 university student; 4 nonworker; 5 retired; 6 driving-age student; 7 school-age child; 8 preschool child",
    "educ": "ABM education proxy by age: 0 under 18; 9 ages 18-21; 13 ages 22 and older",
    "grade": "ABM school category: 2 for SCHG 2-10; 5 for 11-14; 6 for 15-16; 0 otherwise",
    "occen5": "ABM occupation placeholder; always 0",
    "occsoc5": "ABM occupation SOC code derived from the original NAICS2 industry group",
    "indcen": "ABM industry code: 9770 for NAICS2 MIL; 0 otherwise",
    "weeks": _PERSON["WKW"] + _ZERO_IS_NA + "; missing values filled with 0",
    "hours": _PERSON["WKHP"] + _ZERO_IS_NA + "; missing values filled with 0",
    "rac1p": _PERSON["RAC1P"] + "; missing values filled with 0",
    "hisp": "ABM Hispanic flag: 1 for non-Hispanic; 2 otherwise",
    "version": "ABM person version placeholder; always 0",
    "naics2_original_code": "Original NAICS2 industry code as a string; missing values filled with 0",
    "soc2": _PERSON["SOC2"] + "; missing values filled with 0",
}


# PopulationSim's summarize step (populationsim/steps/summarize.py meta_summary)
# writes one row per household control. Each weight column is that control's
# region-wide total at one synthesis stage: sum over seed households of
# (household's incidence for the control x its weight at that stage). The
# region_* columns use the PUMA (seed geography) weights summed over the region.
_WEIGHTED_TOTAL = "Region-wide total for this control using "
FINAL_SUMMARY_REGION = {
    **_RUN_COLUMNS,
    "control_name": "Control target name from populationsim/configs/controls.csv (e.g. Total_HH, Age_5to9)",
    "control_value": "Region-wide control total the synthesis was trying to match",
    "region_preliminary_balanced_weight": _WEIGHTED_TOTAL + "PUMA weights from initial_seed_balancing, before meta control factoring",
    "region_balanced_weight": _WEIGHTED_TOTAL + "PUMA weights after final_seed_balancing (fractional)",
    "region_integer_weight": _WEIGHTED_TOTAL + "PUMA weights after integerize_final_seed_weights (whole households)",
    "mgra_balanced_weight": _WEIGHTED_TOTAL + "MGRA weights from sub_balancing.geography=mgra, before integerizing (fractional)",
    "mgra_integer_weight": _WEIGHTED_TOTAL + "final integerized MGRA weights, i.e. the synthetic population; the Result in silver_control_totals",
}


# E&F mgrabase columns exported by sql/mgrabase.sql. Descriptions come from the
# SANDAG ABM wiki (Input Files: mgra_based_input), the ABM technical
# documentation, and the CVM19 employment sector list.
# Income bands i1-i10 are in the dollar year of the E&F forecast series, and that
# dollar year changes from series to series (older ABM docs list 2007 dollars),
# so the ranges are left out here. Confirm them for the series in use, and don't
# compare bands across series without converting.
_INCOME_BAND = (
    "Households in income band {} of 10 (1 = lowest); band ranges are in the E&F "
    "series' dollar year, which differs between series, so confirm before use"
)
_EMP = "Employment: "
MGRA_BASED_INPUT = {
    **_RUN_COLUMNS,
    "mgra": "MGRA (Master Geographic Reference Area) number",
    "taz": "TAZ (Traffic Analysis Zone) number",
    "LUZ": "Land Use Zone (LUZ) ID",
    "pop": "Total population",
    "hhp": "Total household population (excludes group quarters population)",
    "hs": "Housing structures",
    "hs_sf": "Single-family structures",
    "hs_mf": "Multi-family structures",
    "hs_mh": "Mobile homes",
    "hh": "Total number of households",
    "hh_sf": "Number of households - single family",
    "hh_mf": "Number of households - multi-family",
    "hh_mh": "Number of households - mobile homes",
    "hhs": "Household size",
    "gq_civ": "Group quarters, civilian",
    "gq_mil": "Group quarters, military",
    **{f"i{n}": _INCOME_BAND.format(n) for n in range(1, 11)},
    "emp_gov": _EMP + "Government",
    "emp_mil": _EMP + "Military",
    "emp_ag_min": _EMP + "Agriculture, forestry, fishing and hunting, and mining",
    "emp_bus_svcs": _EMP + "Business services & waste management",
    "emp_fin_res_mgm": _EMP + "FIRE (finance, insurance, real estate) & management of enterprises",
    "emp_educ": _EMP + "Education (private & public)",
    "emp_hlth": _EMP + "Healthcare (private & public)",
    "emp_ret": _EMP + "Retail",
    "emp_trn_wrh": _EMP + "Transportation & warehousing",
    "emp_con": _EMP + "Construction",
    "emp_utl": _EMP + "Utilities",
    "emp_mnf": _EMP + "Manufacturing",
    "emp_whl": _EMP + "Wholesale",
    "emp_ent": _EMP + "Entertainment",
    "emp_accm": _EMP + "Accommodation",
    "emp_food": _EMP + "Food services",
    "emp_oth": _EMP + "Other services",
    "emp_non_ws_wfh": _EMP + "Non-wage/salary, working from home",
    "emp_non_ws_oth": _EMP + "Non-wage/salary, not working from home",
    "emp_total": "Total employment (emp_tot in the E&F mgrabase table)",
    "pseudomsa": "Pseudo MSA classification (regional sub-areas)",
    "zip": "ZIP code",
    "enrollgradekto8": "Grade school K-8 enrollment",
    "enrollgrade9to12": "Grade school 9-12 enrollment",
    "majorcollegeenroll_total": "Major college enrollment",
    "othercollegeenroll_total": "Other college enrollment",
    "hotelroomtotal": "Total number of hotel rooms",
    "parkactive": "Acres of active park",
    "openspaceparkpreserve": "Acres of open park or preserve",
    "beachactive": "Acres of active beach",
    "district27": "District 27 designation",
    "milestocoast": "Distance (miles) to the nearest coast",
    "acre": "Total acres in the MGRA",
    "landacre": "Acres of land in the MGRA",
    "effective_acres": "Effective acres in the MGRA",
    "truckregiontype": "Truck region type",
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
    ("hhid", "BIGINT"),
    ("mgra", "BIGINT"),
    ("serialno", "STRING"),
    ("persons", "INT"),
    ("hinc", "INT"),
    ("hht", "INT"),
    ("presence_of_children", "INT"),
    ("veh", "INT"),
    ("bldgsz", "INT"),
    ("gq_type", "BIGINT"),
    ("num_workers", "INT"),
    ("household_serial_no", "INT"),
    ("taz", "INT"),
    ("hinccat1", "INT"),
    ("unittype", "INT"),
    ("version", "INT"),
    ("poverty", "DOUBLE"),
] + _RUN_TIMESTAMP

SYNTHETIC_PERSON_TYPES = _RUN_ID + [
    ("mgra", "BIGINT"),
    ("hhid", "BIGINT"),
    ("serialno", "STRING"),
    ("pnum", "INT"),
    ("age", "INT"),
    ("sex", "BIGINT"),
    ("employment_status", "INT"),
    ("class_of_worker", "INT"),
    ("hours", "INT"),
    ("school_grade", "BIGINT"),
    ("rac1p", "BIGINT"),
    ("hispanic_origin", "BIGINT"),
    ("military_service", "INT"),
    ("education_attainment", "INT"),
    ("occupation_code", "INT"),
    ("weeks", "INT"),
    ("naics_industry_code", "STRING"),
    ("naics_2digit", "STRING"),
    ("soc_occupation_code", "STRING"),
    ("soc2", "INT"),
    ("perid", "BIGINT"),
    ("household_serial_no", "INT"),
    ("miltary", "INT"),
    ("pemploy", "INT"),
    ("pstudent", "INT"),
    ("ptype", "INT"),
    ("educ", "INT"),
    ("grade", "INT"),
    ("occen5", "INT"),
    ("occsoc5", "STRING"),
    ("indcen", "INT"),
    ("hisp", "INT"),
    ("version", "INT"),
    ("naics2_original_code", "STRING"),
] + _RUN_TIMESTAMP

# Weighted totals are fractional at some stages, so all are DOUBLE; the silver
# table casts to these types since pandas may write whole-number columns as BIGINT.
FINAL_SUMMARY_REGION_WEIGHTS = [
    "region_preliminary_balanced_weight",
    "region_balanced_weight",
    "region_integer_weight",
    "mgra_balanced_weight",
    "mgra_integer_weight",
]
FINAL_SUMMARY_REGION_TYPES = _RUN_ID + [
    ("control_name", "STRING"),
    ("control_value", "DOUBLE"),
] + [(c, "DOUBLE") for c in FINAL_SUMMARY_REGION_WEIGHTS] + _RUN_TIMESTAMP

# Types follow the E&F mgrabase table (int/smallint -> INT, float -> DOUBLE), in
# sql/mgrabase.sql column order. The CSV/parquet round trip can change them (e.g.
# int to BIGINT), so the silver table casts to these.
_MGRA_DOUBLE = {
    "hhs", "parkactive", "openspaceparkpreserve", "beachactive",
    "milestocoast", "acre", "landacre", "effective_acres",
}
MGRA_BASED_INPUT_COLUMNS = [
    c for c in MGRA_BASED_INPUT if c not in ("run_id", "year", "run_timestamp")
]
MGRA_BASED_INPUT_TYPES = _RUN_ID + [
    (c, "DOUBLE" if c in _MGRA_DOUBLE else "INT") for c in MGRA_BASED_INPUT_COLUMNS
] + _RUN_TIMESTAMP
