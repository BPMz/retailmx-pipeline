import json
import os
from io import BytesIO
from pathlib import Path

import pandas as pd
import pyodbc
import yaml
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "data-generation" / "config"

TABLES = [
    "MSTR_PROVEEDORES",
    "MSTR_ARTICULOS",
    "MSTR_TIENDAS",
    "CRM_MIEMBROS",
    "TRANS_VENTAS",
    "INV_STOCK_DIARIO",
    "POST_DEVOLUCIONES",
]

PRIMARY_KEYS = {
    "MSTR_PROVEEDORES": "id_proveedor",
    "MSTR_ARTICULOS": "art_id",
    "MSTR_TIENDAS": "id_tienda",
    "CRM_MIEMBROS": "id_miembro",
    "TRANS_VENTAS": "id_trans",
    "INV_STOCK_DIARIO": "id_snapshot",
    "POST_DEVOLUCIONES": "id_devolucion",
}

load_dotenv(PROJECT_ROOT / ".env")


def get_sql_connection():
    """Conexión con Azure SQL."""

    required = [
        "AZURE_SQL_SERVER",
        "AZURE_SQL_DATABASE",
        "AZURE_SQL_USERNAME",
        "AZURE_SQL_PASSWORD",
    ]

    missing = [
        variable
        for variable in required
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


def get_blob_service():
    """Conexión con Azure Storage."""

    connection_string = os.getenv(
        "AZURE_STORAGE_CONNECTION_STRING"
    )

    if not connection_string:
        raise ValueError(
            "Falta AZURE_STORAGE_CONNECTION_STRING en .env"
        )

    return BlobServiceClient.from_connection_string(
        connection_string
    )


def load_yaml(file_name):
    """Lee un YAML de configuración."""

    with open(
        CONFIG_DIR / file_name,
        encoding="utf-8",
    ) as file:
        return yaml.safe_load(file)


def upload_parquet(dataframe, container, blob_name):
    """Guarda un DataFrame como Parquet."""

    buffer = BytesIO()
    dataframe.to_parquet(buffer, index=False)

    file_size = buffer.getbuffer().nbytes
    buffer.seek(0)

    blob_client = get_blob_service().get_blob_client(
        container=container,
        blob=blob_name,
    )

    blob_client.upload_blob(
        buffer,
        overwrite=True,
    )

    return file_size


def read_parquet_prefix(container, prefix):
    """Lee los archivos Parquet de una ruta."""

    container_client = (
        get_blob_service()
        .get_container_client(container)
    )

    dataframes = []

    for blob in container_client.list_blobs(
        name_starts_with=prefix
    ):
        if blob.name.endswith(".parquet"):
            content = container_client.download_blob(
                blob.name
            ).readall()

            dataframes.append(
                pd.read_parquet(BytesIO(content))
            )

    if not dataframes:
        return pd.DataFrame()

    return pd.concat(
        dataframes,
        ignore_index=True,
    )


def save_json(data, container, blob_name):
    """Guarda un JSON en Azure Storage."""

    content = json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    blob_client = get_blob_service().get_blob_client(
        container=container,
        blob=blob_name,
    )

    blob_client.upload_blob(
        content,
        overwrite=True,
    )


def load_json(container, blob_name, default=None):
    """Lee un JSON de Azure Storage."""

    blob_client = get_blob_service().get_blob_client(
        container=container,
        blob=blob_name,
    )

    if not blob_client.exists():
        return default

    content = blob_client.download_blob().readall()

    return json.loads(
        content.decode("utf-8")
    )