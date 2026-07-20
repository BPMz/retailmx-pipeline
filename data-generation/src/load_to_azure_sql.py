import os
import time
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

MAX_CONNECTION_ATTEMPTS = 4

def get_connection():
    """Conecta con Azure SQL e intenta nuevamente si no responde."""

    load_dotenv(
        PROJECT_ROOT / ".env",
        override=True,
    )

    required_variables = [
        "AZURE_SQL_SERVER",
        "AZURE_SQL_DATABASE",
        "AZURE_SQL_USERNAME",
        "AZURE_SQL_PASSWORD",
    ]

    missing = [
        variable
        for variable in required_variables
        if not os.getenv(variable)
    ]

    if missing:
        raise ValueError(
            f"Faltan variables en .env: {', '.join(missing)}"
        )

    driver = os.getenv(
        "AZURE_SQL_DRIVER",
        "ODBC Driver 18 for SQL Server",
    )

    server = os.getenv("AZURE_SQL_SERVER").strip()
    database = os.getenv("AZURE_SQL_DATABASE").strip()
    username = os.getenv("AZURE_SQL_USERNAME").strip()
    password = os.getenv("AZURE_SQL_PASSWORD")

    connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER=tcp:{server},1433;"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=60;"
    )

    for attempt in range(1, MAX_CONNECTION_ATTEMPTS + 1):
        try:
            print(
                f"Conectando con Azure SQL "
                f"- intento {attempt}..."
            )

            connection = pyodbc.connect(connection_string)

            print("Conexión con Azure SQL exitosa.")
            return connection

        except pyodbc.OperationalError:
            if attempt == MAX_CONNECTION_ATTEMPTS:
                print(
                    "No fue posible conectar con Azure SQL "
                    "después de varios intentos."
                )
                raise

            wait_seconds = attempt * 15

            print(
                "Azure SQL todavía no responde. "
                f"Nuevo intento en {wait_seconds} segundos."
            )

            time.sleep(wait_seconds)


def clean_value(value):
    """Convierte valores de Pandas a valores compatibles con SQL."""

    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        return value.item()

    return value


def clear_tables(cursor):
    """Elimina los datos actuales respetando las dependencias."""

    for table in reversed(TABLES):
        cursor.execute(
            f"DELETE FROM [source].[{table}]"
        )

    print("Tablas limpiadas correctamente.")


def load_table(cursor, table):
    """Carga una tabla desde su archivo CSV."""

    csv_path = CSV_DIR / f"{table}.csv"

    if not csv_path.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {csv_path}"
        )

    dataframe = pd.read_csv(
        csv_path,
        encoding="utf-8",
    )

    columns = ", ".join(
        f"[{column}]"
        for column in dataframe.columns
    )

    placeholders = ", ".join(
        "?"
        for _ in dataframe.columns
    )

    query = (
        f"INSERT INTO [source].[{table}] "
        f"({columns}) "
        f"VALUES ({placeholders})"
    )

    rows = [
        tuple(
            clean_value(value)
            for value in row
        )
        for row in dataframe.itertuples(
            index=False,
            name=None,
        )
    ]

    cursor.executemany(query, rows)

    print(
        f"{table}: {len(rows):,} registros cargados."
    )


def main():
    """Limpia y vuelve a cargar las siete tablas fuente."""

    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.fast_executemany = True

        clear_tables(cursor)

        for table in TABLES:
            load_table(cursor, table)

        connection.commit()

        print("Carga hacia Azure SQL finalizada correctamente.")

    except Exception:
        connection.rollback()

        print("La carga fue cancelada por un error.")
        print("Los cambios fueron revertidos.")
        
        raise

    finally:
        connection.close()
        print("Conexión con Azure SQL cerrada.")


if __name__ == "__main__":
    main()