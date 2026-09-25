from pyspark import pipelines as dp
from pyspark.sql import functions as F


@dp.table(
    comment="Cleaned synthetic persons with standardized column names and types",
    table_properties={"delta.feature.timestampNtz": "supported"},
)
@dp.expect_or_drop("valid_household_id", "household_id IS NOT NULL")
@dp.expect_or_drop("valid_mgra", "mgra IS NOT NULL")
def silver_synthetic_persons():
    lookup = spark.read.table("run_id_lookup")
    return (
        spark.readStream.table("bronze_synthetic_persons")
        .drop("_rescued_data")
        .withColumn("year", F.col("year").cast("int"))
        .join(lookup, ["run_timestamp", "year"], "left")
        .transform(lambda df: df.select(
            "run_id",
            *[c for c in df.columns if c not in ("run_id", "run_timestamp")],
            "run_timestamp",
        ))
        .withColumnsRenamed({
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
        })
        .withColumns({
            "person_order": F.col("person_order").cast("int"),
            "age": F.col("age").cast("int"),
            "employment_status": F.col("employment_status").cast("int"),
            "class_of_worker": F.col("class_of_worker").cast("int"),
            "work_hours_per_week": F.col("work_hours_per_week").cast("int"),
            "military_service": F.col("military_service").cast("int"),
            "education_attainment": F.col("education_attainment").cast("int"),
            "occupation_code": F.col("occupation_code").cast("int"),
            "weeks_worked": F.col("weeks_worked").cast("int"),
            "soc_2digit": F.col("soc_2digit").cast("int"),
        })
    )
