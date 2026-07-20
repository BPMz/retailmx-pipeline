from pathlib import Path

import pandas as pd


def export_tables(
    tables: dict[str, pd.DataFrame],
    output_path: Path,
    formats: list[str],
) -> list[Path]:
    """Exporta todas las tablas en los formatos configurados."""
    written_files: list[Path] = []

    for file_format in formats:
        if file_format not in {"csv", "parquet"}:
            raise ValueError(
                f"Formato no soportado: {file_format}"
            )

        format_path = output_path / file_format
        format_path.mkdir(parents=True, exist_ok=True,)

        for table_name, dataframe in tables.items():
            file_path = (format_path / f"{table_name}.{file_format}" )

            if file_format == "csv":
                dataframe.to_csv(file_path, index=False, encoding="utf-8",)
            else:
                dataframe.to_parquet(file_path, index=False,)

            written_files.append(file_path)

    return written_files