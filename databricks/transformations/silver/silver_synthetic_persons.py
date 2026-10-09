from pyspark import pipelines as dp
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window

from utilities.column_comments import (
    SYNTHETIC_PERSON_RENAMES,
    SYNTHETIC_PERSON_TYPES,
    SYNTHETIC_PERSONS,
    schema_ddl,
)


def process_persons(persons: DataFrame) -> DataFrame:
    """Add ABM3 person fields and sequential person IDs within each run."""
    age = F.col("age")
    school_grade = F.col("school_grade")
    industry = F.col("naics_2digit")
    persons = persons.withColumns({
        "household_serial_no": F.lit(0),
        "version": F.lit(0),
        "perid": F.row_number().over(
            Window.partitionBy("run_id").orderBy("hhid", "pnum")
        ).cast("bigint"),
        "pemploy": F.when(age < 16, 4)
            .when((age >= 16) & F.col("employment_status").isin(3, 6), 3)
            .when((age >= 16) & (F.col("hours") >= 35), 1)
            .otherwise(2),
        "grade": F.when(school_grade.between(2, 10), 2)
            .when(school_grade.between(11, 14), 5)
            .when(school_grade.isin(15, 16), 6).otherwise(0),
        "hisp": F.when(F.col("hispanic_origin") == 1, 1).otherwise(2),
        "miltary": F.when(F.col("military_service") == 1, 1).otherwise(0),
        "educ": F.when(age >= 22, 13).when(age >= 18, 9).otherwise(0),
        "occen5": F.lit(0),
        "indcen": F.when(industry == "MIL", 9770).otherwise(0),
        "occsoc5": F.when(industry.isin("21", "23", "48", "49", "4M", "52", "53", "54", "55", "56"), "11-1021")
            .when(industry.isin("51", "61", "62", "92"), "31-1010")
            .when(industry.isin("42", "44", "45", "721", "722"), "41-1011")
            .when(industry.isin("11", "81"), "45-1010")
            .when(industry.isin("22", "31", "32", "33", "3M", "71"), "51-1011")
            .when(industry == "MIL", "55-1010").otherwise("00-0000"),
        "weeks": F.coalesce(F.col("weeks"), F.lit(0)).cast("int"),
        "hours": F.coalesce(F.col("hours"), F.lit(0)).cast("int"),
        "rac1p": F.coalesce(F.col("rac1p"), F.lit(0)),
        "naics2_original_code": F.coalesce(industry, F.lit("0")),
        "soc2": F.coalesce(F.col("soc2"), F.lit(0)).cast("int"),
    })
    employment = F.col("pemploy")
    persons = persons.withColumn(
        "pstudent",
        F.when((employment == 1) | (school_grade < 1),
               F.when(age < 16, 1).otherwise(3))
        .when((school_grade >= 15) & (employment != 1),
              F.when(age < 16, 1).when(age >= 16, 2).otherwise(3))
        .when(school_grade.between(1, 14) & (employment != 1),
              F.when(age <= 19, 1).when(age > 19, 2).otherwise(3))
        .otherwise(3),
    )
    student = F.col("pstudent")
    return persons.withColumn(
        "ptype",
        F.when(employment == 1, 1)
        .when((student == 3) & (employment == 2), 2)
        .when((student == 3) & (age >= 65) & employment.isin(3, 4), 5)
        .when((student == 3) & (age < 6) & employment.isin(3, 4), 8)
        .when((student == 2) & employment.isin(2, 3, 4), 3)
        .when((student == 1) & (age < 6) & employment.isin(2, 3, 4), 8)
        .when((student == 1) & (age >= 16) & employment.isin(2, 3, 4), 6)
        .when((student == 1) & (age >= 6) & (age < 16) & employment.isin(2, 3, 4), 7)
        .otherwise(4),
    )


@dp.materialized_view(
    comment="Cleaned synthetic persons with standardized columns and ABM3 person fields",
    schema=schema_ddl(SYNTHETIC_PERSON_TYPES, SYNTHETIC_PERSONS),
    table_properties={"delta.feature.timestampNtz": "supported"},
)
@dp.expect_or_drop("valid_household_id", "hhid IS NOT NULL")
@dp.expect_or_drop("valid_mgra", "mgra IS NOT NULL")
# Data quality: drop rows with no run_id. run_id_lookup is built from this table,
# so this should never fire; kept for consistency with the other silver tables
@dp.expect_or_drop("valid_run_id", "run_id IS NOT NULL")
def silver_synthetic_persons():
    lookup = spark.read.table("run_id_lookup")
    persons = (
        spark.read.table("bronze_synthetic_persons")
        .drop("_rescued_data")
        .withColumn("year", F.col("year").cast("int"))
        .join(lookup, ["run_timestamp", "year"], "left")
        .transform(lambda df: df.select(
            "run_id",
            *[c for c in df.columns if c not in ("run_id", "run_timestamp")],
            "run_timestamp",
        ))
        .withColumnsRenamed(SYNTHETIC_PERSON_RENAMES)
        .withColumns({
            "pnum": F.col("pnum").cast("int"),
            "age": F.col("age").cast("int"),
            "employment_status": F.col("employment_status").cast("int"),
            "class_of_worker": F.col("class_of_worker").cast("int"),
            "hours": F.col("hours").cast("int"),
            "military_service": F.col("military_service").cast("int"),
            "education_attainment": F.col("education_attainment").cast("int"),
            "occupation_code": F.col("occupation_code").cast("int"),
            "weeks": F.col("weeks").cast("int"),
            "soc2": F.col("soc2").cast("int"),
        })
    )
    return process_persons(persons).select(
        *[column for column, _ in SYNTHETIC_PERSON_TYPES]
    )
