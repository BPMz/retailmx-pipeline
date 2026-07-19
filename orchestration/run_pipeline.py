import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path



PROJECT_ROOT = Path(__file__).resolve().parents[1]


EVIDENCE_DIR = PROJECT_ROOT / "docs" / "evidence"
LOG_FILE = EVIDENCE_DIR / "04_pipeline_ejecucion.txt"
SUMMARY_FILE = EVIDENCE_DIR / "04_pipeline_resumen.md"


RETRIES = 3
TIMEOUT_SECONDS = 1800  

TASKS = [
    ("Bronze", "pipelines.bronze.bronze"),
    ("Silver", "pipelines.silver.silver"),
    ("Gold", "pipelines.gold.gold"),
]


def write_log(message):
    """Muestra y guarda un mensaje en el log."""

    print(message)

    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(message + "\n")


def run_task(task_name, module_name):
    """Ejecuta una tarea con reintentos."""

    for attempt in range(1, RETRIES + 2):
        write_log("")
        write_log(f"Ejecutando {task_name} - intento {attempt}")

        start_time = time.perf_counter()

        try:
            result = subprocess.run(
                [sys.executable, "-m", module_name],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                encoding="utf-8",
                errors="replace",
            )

            if result.stdout:
                write_log(result.stdout.strip())

            if result.stderr:
                write_log(result.stderr.strip())

            duration = time.perf_counter() - start_time

            if result.returncode == 0:
                write_log(
                    f"{task_name} finalizada correctamente "
                    f"en {duration:.2f} segundos."
                )

                return {
                    "task": task_name,
                    "status": "Exitoso",
                    "duration": duration,
                    "attempts": attempt,
                }

            write_log(
                f"{task_name} terminó con error. "
                f"Código de salida: {result.returncode}"
            )

        except subprocess.TimeoutExpired:
            duration = time.perf_counter() - start_time

            write_log(
                f"{task_name} superó el tiempo máximo "
                f"de {TIMEOUT_SECONDS // 60} minutos."
            )

        except Exception as error:
            duration = time.perf_counter() - start_time
            write_log(f"Error inesperado en {task_name}: {error}")

        if attempt <= RETRIES:
            wait_seconds = 2 ** (attempt - 1)

            write_log(
                f"Nuevo intento en {wait_seconds} segundos..."
            )

            time.sleep(wait_seconds)

    return {
        "task": task_name,
        "status": "Fallido",
        "duration": duration,
        "attempts": RETRIES + 1,
    }


def save_summary(start_date, end_date, results, pipeline_status):
    """Guarda el resumen de la ejecución en Markdown."""

    total_duration = sum(
        result["duration"] for result in results
    )

    lines = [
        "# RetailMax - Resumen de ejecución",
        "",
        f"- Fecha de inicio: {start_date:%Y-%m-%d %H:%M:%S}",
        f"- Fecha de finalización: {end_date:%Y-%m-%d %H:%M:%S}",
        f"- Estado general: **{pipeline_status}**",
        f"- Duración total: {total_duration:.2f} segundos",
        "",
        "## Resultado por tarea",
        "",
        "| Tarea | Estado | Duración | Intentos |",
        "|---|---|---:|---:|",
    ]

    for result in results:
        lines.append(
            f"| {result['task']} "
            f"| {result['status']} "
            f"| {result['duration']:.2f} segundos "
            f"| {result['attempts']} |"
        )

    SUMMARY_FILE.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main():
    """Ejecuta Bronze, Silver y Gold en orden."""

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    LOG_FILE.write_text("", encoding="utf-8")

    start_date = datetime.now()
    results = []
    pipeline_status = "Exitoso"

    write_log("=" * 55)
    write_log("RetailMax - Pipeline Medallion")
    write_log("=" * 55)
    write_log(
        f"Inicio: {start_date:%Y-%m-%d %H:%M:%S}"
    )
    write_log("Flujo: Bronze -> Silver -> Gold")

    for task_name, module_name in TASKS:
        result = run_task(task_name, module_name)
        results.append(result)

        if result["status"] == "Fallido":
            pipeline_status = "Fallido"

            write_log("")
            write_log(
                f"Pipeline detenido porque falló {task_name}."
            )

            break

    end_date = datetime.now()

    save_summary(
        start_date,
        end_date,
        results,
        pipeline_status,
    )

    write_log("")
    write_log("=" * 55)
    write_log(f"Estado final: {pipeline_status}")
    write_log(
        f"Finalización: {end_date:%Y-%m-%d %H:%M:%S}"
    )
    write_log(f"Resumen: {SUMMARY_FILE}")
    write_log("=" * 55)

    if pipeline_status == "Fallido":
        sys.exit(1)


if __name__ == "__main__":
    main()