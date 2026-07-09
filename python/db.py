from pathlib import Path
import yaml
import sqlalchemy as sql


def get_engine(database=None):
    secrets_path = Path(__file__).parent.parent / "secrets.yml"
    with open(secrets_path, "r") as file:
        secrets = yaml.safe_load(file)

    dbname = database or secrets["sql"]["output_database"]

    return sql.create_engine(
        "mssql+pyodbc://@"
        + secrets["sql"]["server"]
        + "/"
        + dbname
        + "?trusted_connection=yes"
        + "&driver=ODBC Driver 18 for SQL Server"
        + "&TrustServerCertificate=yes",
        fast_executemany=True,
    )