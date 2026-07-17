from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd


def export_tables(
    tables: dict[str, pd.DataFrame],
    output_path: Path,
    formats: list[str],
) -> list[Path]:
    """
    Exporta todas las tablas en los formatos configurados.
    """
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


def _run_self_test() -> None:
    """
    Comprueba la exportación a CSV y Parquet.
    """
    tables = {
        "TEST_TABLE": pd.DataFrame(
            {
                "id": [1, 2, 3],
                "valor": [100, 200, 300],
            }
        )
    }

    with TemporaryDirectory() as directory:
        files = export_tables(
            tables=tables,
            output_path=Path(directory),
            formats=["csv", "parquet"],
        )

        assert len(files) == 2
        assert all(file_path.exists()
            for file_path in files
        )

        print("\nArchivos exportados:")

        for file_path in files:
            print(file_path.name)

    print("\nPrueba de export_data.py " "completada correctamente.")


if __name__ == "__main__":
    _run_self_test()