from pathlib import Path

REPORT_DIR = Path(__file__).resolve().parents[2] / "docs/evidence"

def save_quality_report(run_id, results):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / f"reporte_calidad_silver_{run_id}.md"
    lines = ["# RetailMax - Reporte de calidad Silver", ""]

    for item in results:
        total, valid = item["total"], item["valid"]
        percentage = valid / total * 100 if total else 0
        lines += [
            f"## Tabla: {item['table']}",
            f"- Registros totales: {total:,}",
            f"- Registros rechazados: {item['rejected']:,}",
            f"- Registros conformes: {valid:,}",
            f"- Porcentaje conforme: {percentage:.2f}%",
            "### Porcentaje de nulos por columna",
        ]
        for col, value in item["null_percentages"].items():
            lines.append(f"- `{col}`: {value:.2f}%")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
