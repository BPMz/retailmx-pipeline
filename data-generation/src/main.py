from pathlib import Path

# Este script es el punto de entrada para la generación de datos fuente. Ejecuta todo el proceso de generación, introducción de anomalías y exportación de los datos generados.
from src.anomalies import inject_anomalies
from src.config import load_project_configuration
from src.export_data import export_tables
from src.generate_data import generate_source_data


def main() -> None:
    """
    Ejecuta la generación completa de datos fuente.
    """
    project_root = Path(__file__).resolve().parents[1]

    config, reference_data = load_project_configuration(project_root)

    print("Generando tablas...")

    tables = generate_source_data(config=config, reference_data=reference_data,)

    print("Introduciendo anomalías...")

    tables, anomaly_report = inject_anomalies(tables=tables, config=config,)

    output_path = (
        project_root / config["paths"]["source"])

    print("Exportando CSV y Parquet...")

    written_files = export_tables(tables=tables, output_path=output_path, formats=config["output"]["formats"],)

    anomaly_report_path = (output_path / "anomaly_report.csv")

    anomaly_report.to_csv(anomaly_report_path, index=False, encoding="utf-8",)

    print("\nTablas generadas:")

    for table_name, dataframe in tables.items():
        print(f"{table_name}: " f"{len(dataframe):,} registros")

    print("\nArchivos exportados:", len(written_files),)

    print("Reporte de anomalías:", anomaly_report_path,)

    print("\nProceso completado correctamente.")


if __name__ == "__main__":
    main()