#Realiza la carga de los datos desde los CSV hacia esas tablas. Punto 2 Fase 1
import os
from pathlib import Path

import pandas as pd
import pyodbc
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSV_DIR = PROJECT_ROOT / "data-generation" / "output" / "csv"

TABLES = [
    "MSTR_PROVEEDORES",
    "MSTR_ARTICULOS",
    "MSTR_TIENDAS",
    "CRM_MIEMBROS",
    "TRANS_VENTAS",
    "INV_STOCK_DIARIO",
    "POST_DEVOLUCIONES",
]


def get_connection():
    load_dotenv(PROJECT_ROOT / ".env")

    variables = [
        "AZURE_SQL_SERVER",
        "AZURE_SQL_DATABASE",
        "AZURE_SQL_USERNAME",
        "AZURE_SQL_PASSWORD",
    ]

    missing = [name for name in variables if not os.getenv(name)]

    if missing:
        raise ValueError(
            f"Faltan variables en .env: {', '.join(missing)}"
        )

    driver = os.getenv(
        "AZURE_SQL_DRIVER",
        "ODBC Driver 18 for SQL Server",
    )

    connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER=tcp:{os.getenv('AZURE_SQL_SERVER')},1433;"
        f"DATABASE={os.getenv('AZURE_SQL_DATABASE')};"
        f"UID={os.getenv('AZURE_SQL_USERNAME')};"
        f"PWD={os.getenv('AZURE_SQL_PASSWORD')};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=60;"
    )

    return pyodbc.connect(connection_string)


def clean_value(value):
    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        return value.item()

    return value


def clear_tables(cursor):
    for table in reversed(TABLES):
        cursor.execute(f"DELETE FROM [source].[{table}]")

    print("Tablas limpiadas correctamente.")


def load_table(cursor, table):
    csv_path = CSV_DIR / f"{table}.csv"

    if not csv_path.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo {csv_path.name}"
        )

    dataframe = pd.read_csv(csv_path)

    columns = ", ".join(
        f"[{column}]" for column in dataframe.columns
    )
    placeholders = ", ".join(
        "?" for _ in dataframe.columns
    )

    query = (
        f"INSERT INTO [source].[{table}] ({columns}) "
        f"VALUES ({placeholders})"
    )

    rows = [
        tuple(clean_value(value) for value in row)
        for row in dataframe.itertuples(index=False, name=None)
    ]

    cursor.executemany(query, rows)

    print(f"{table}: {len(rows):,} registros cargados.")


def main():
    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.fast_executemany = True

        clear_tables(cursor)

        for table in TABLES:
            load_table(cursor, table)

        connection.commit()
        print("Carga finalizada correctamente.")

    except Exception:
        connection.rollback()
        print("La carga fue cancelada por un error.")
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()