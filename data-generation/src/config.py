from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

# tablas requeridas para la generación de datos.
REQUIRED_TABLES = {
    "proveedores",
    "articulos",
    "tiendas",
    "miembros",
    "ventas",
    "stock",
    "devoluciones",
}

REQUIRED_CATALOGS = {
    "countries",
    "locations",
    "store_types",
    "sales_channels",
    "payment_types",
    "genders",
    "units_of_measure",
    "categories",
    "return_reasons",
    "return_statuses",
}

SUPPORTED_FORMATS = {
    "csv",
    "parquet",
}

# Funcion para cargar un archivo YAML y devolver su contenido como un diccionario.
def load_yaml(file_path: Path) -> dict[str, Any]:
    """ Lee un archivo YAML y devuelve su contenido. """
    if not file_path.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {file_path}"
        )

    with file_path.open("r", encoding="utf-8") as file:
        content = yaml.safe_load(file)

    if not isinstance(content, dict):
        raise ValueError(
            f"El archivo {file_path.name} está vacío "
            "o no contiene una estructura válida."
        )

    return content


def validate_probability(
    value: Any,
    field_name: str,
) -> None:
    """ Comprueba que una probabilidad esté entre 0 y 1."""
    if not isinstance(value, (int, float)):
        raise ValueError(
            f"'{field_name}' debe ser un número."
        )

    if not 0 <= float(value) <= 1:
        raise ValueError(
            f"'{field_name}' debe estar entre 0 y 1."
        )


def validate_generation_config(
    config: dict[str, Any],
) -> None:
    """Valida los parámetros principales de generation_config.yaml. """
    project = config.get("project")

    if not isinstance(project, dict):
        raise ValueError(
            "Falta la sección 'project'."
        )

    if not isinstance(project.get("seed"), int):
        raise ValueError(
            "'project.seed' debe ser un número entero."
        )

    if not isinstance(project.get("locale"), str):
        raise ValueError(
            "'project.locale' debe ser un texto."
        )

    tables = config.get("tables")

    if not isinstance(tables, dict):
        raise ValueError(
            "Falta la sección 'tables'."
        )

    missing_tables = REQUIRED_TABLES.difference(tables)

    if missing_tables:
        raise ValueError(
            "Faltan volúmenes para las tablas: "
            + ", ".join(sorted(missing_tables))
        )

    for table_name in REQUIRED_TABLES:
        row_count = tables[table_name]

        if not isinstance(row_count, int) or row_count <= 0:
            raise ValueError(
                f"'tables.{table_name}' debe ser "
                "un entero mayor que cero."
            )

    date_range = config.get("date_range")

    if not isinstance(date_range, dict):
        raise ValueError(
            "Falta la sección 'date_range'."
        )

    try:
        start_date = datetime.strptime(
            date_range["start_date"],
            "%Y-%m-%d",
        ).date()

        end_date = datetime.strptime(
            date_range["end_date"],
            "%Y-%m-%d",
        ).date()

    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(
            "Las fechas deben utilizar el formato YYYY-MM-DD."
        ) from error

    if start_date >= end_date:
        raise ValueError(
            "'start_date' debe ser anterior a 'end_date'."
        )

    if (end_date - start_date).days < 365:
        raise ValueError(
            "El rango de fechas debe cubrir al menos doce meses."
        )

    paths = config.get("paths")

    if not isinstance(paths, dict) or not paths.get("source"):
        raise ValueError(
            "Falta el campo 'paths.source'."
        )

    output = config.get("output")

    if not isinstance(output, dict):
        raise ValueError(
            "Falta la sección 'output'."
        )

    formats = output.get("formats")

    if not isinstance(formats, list):
        raise ValueError(
            "'output.formats' debe ser una lista."
        )

    normalized_formats = {
        str(file_format).lower()
        for file_format in formats
    }

    if len(normalized_formats) < 2:
        raise ValueError(
            "Deben configurarse al menos dos formatos de salida."
        )

    unsupported_formats = (
        normalized_formats - SUPPORTED_FORMATS
    )

    if unsupported_formats:
        raise ValueError(
            "Formatos no soportados: "
            + ", ".join(sorted(unsupported_formats))
        )

    data_quality = config.get("data_quality")

    if not isinstance(data_quality, dict):
        raise ValueError(
            "Falta la sección 'data_quality'."
        )

    validate_probability(
        data_quality.get("null_percentage"),
        "data_quality.null_percentage",
    )

    anomalies = config.get("anomalies")

    if not isinstance(anomalies, dict):
        raise ValueError(
            "Falta la sección 'anomalies'."
        )

    if not isinstance(anomalies.get("enabled"), bool):
        raise ValueError(
            "'anomalies.enabled' debe ser true o false."
        )

    anomaly_fields = [
        "duplicate_sales_rate",
        "out_of_range_dates_rate",
        "inconsistent_returns_rate",
    ]

    for field_name in anomaly_fields:
        validate_probability(
            anomalies.get(field_name),
            f"anomalies.{field_name}",
        )


def validate_reference_data(
    reference_data: dict[str, Any],
) -> None:
    """Comprueba que existan los catálogos necesarios."""
    missing_catalogs = REQUIRED_CATALOGS.difference(
        reference_data
    )

    if missing_catalogs:
        raise ValueError(
            "Faltan catálogos en reference_data.yaml: "
            + ", ".join(sorted(missing_catalogs))
        )

    for catalog_name in REQUIRED_CATALOGS:
        if not reference_data[catalog_name]:
            raise ValueError(
                f"El catálogo '{catalog_name}' está vacío."
            )

    for location in reference_data["locations"]:
        required_fields = {
            "id_ciudad",
            "id_pais",
            "ciudad",
            "pais",
        }

        missing_fields = required_fields.difference(location)

        if missing_fields:
            raise ValueError(
                "Una ubicación no contiene los campos: "
                + ", ".join(sorted(missing_fields))
            )


def load_project_configuration(
    project_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Carga y valida los archivos de configuración del proyecto."""
    config_path = (
        project_root
        / "config"
        / "generation_config.yaml"
    )

    reference_path = (
        project_root
        / "config"
        / "reference_data.yaml"
    )

    config = load_yaml(config_path)
    reference_data = load_yaml(reference_path)

    validate_generation_config(config)
    validate_reference_data(reference_data)

    return config, reference_data