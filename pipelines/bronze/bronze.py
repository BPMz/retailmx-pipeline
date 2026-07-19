from time import perf_counter

import pandas as pd

from pipelines.common.utils import (
    PRIMARY_KEYS,
    TABLES,
    get_sql_connection,
    load_json,
    save_json,
    upload_parquet,
)


CONTAINER = "bronze"
STATE_FILE = "_control/change_tracking_state.json"


def read_table(
    connection,
    table,
    last_version,
    current_version,
):
    """Lee toda la tabla o solo sus cambios."""

    cursor = connection.cursor()

    if last_version is None:
        query = f"SELECT * FROM [source].[{table}]"
        cursor.execute(query)

    else:
        primary_key = PRIMARY_KEYS[table]

        query = f"""
            SELECT source.*
            FROM CHANGETABLE(
                CHANGES [source].[{table}], ?
            ) AS changes
            INNER JOIN [source].[{table}] AS source
                ON source.[{primary_key}]
                = changes.[{primary_key}]
            WHERE changes.SYS_CHANGE_OPERATION IN ('I', 'U')
              AND changes.SYS_CHANGE_VERSION <= ?
        """

        cursor.execute(
            query,
            last_version,
            current_version,
        )

    columns = [
        column[0]
        for column in cursor.description
    ]

    rows = cursor.fetchall()

    return pd.DataFrame.from_records(
        [tuple(row) for row in rows],
        columns=columns,
    )


def run_bronze():
    """Ejecuta la carga inicial o incremental."""

    ingestion_time = pd.Timestamp.now(tz="UTC")
    run_id = ingestion_time.strftime("%Y%m%dT%H%M%S")

    partition = ingestion_time.strftime(
        "year=%Y/month=%m/day=%d"
    )

    state = load_json(
        CONTAINER,
        STATE_FILE,
        default={},
    ) or {}

    connection = get_sql_connection()
    logs = []

    try:
        cursor = connection.cursor()

        cursor.execute(
            "SELECT CHANGE_TRACKING_CURRENT_VERSION()"
        )

        current_version = cursor.fetchone()[0]

        if current_version is None:
            raise RuntimeError(
                "Change Tracking no está habilitado."
            )

        current_version = int(current_version)

        for table in TABLES:
            started = perf_counter()

            try:
                dataframe = read_table(
                    connection,
                    table,
                    state.get(table),
                    current_version,
                )

                batch_id = (
                    f"{run_id}_{table.lower()}"
                )

                file_size = 0

                if not dataframe.empty:
                    dataframe["ingestion_timestamp"] = (
                        ingestion_time
                    )
                    dataframe["source_system"] = (
                        "Azure SQL Database"
                    )
                    dataframe["batch_id"] = batch_id

                    blob_name = (
                        f"{table}/{partition}/"
                        f"{batch_id}.parquet"
                    )

                    file_size = upload_parquet(
                        dataframe,
                        CONTAINER,
                        blob_name,
                    )

                logs.append(
                    {
                        "batch_id": batch_id,
                        "table_name": table,
                        "records_processed": len(dataframe),
                        "file_size_bytes": file_size,
                        "duration_seconds": round(
                            perf_counter() - started,
                            2,
                        ),
                        "status": "success",
                        "execution_timestamp": ingestion_time,
                        "error_message": None,
                    }
                )

                state[table] = current_version

                print(
                    f"{table}: "
                    f"{len(dataframe):,} registros"
                )

            except Exception as error:
                logs.append(
                    {
                        "batch_id": run_id,
                        "table_name": table,
                        "records_processed": 0,
                        "file_size_bytes": 0,
                        "duration_seconds": round(
                            perf_counter() - started,
                            2,
                        ),
                        "status": "failed",
                        "execution_timestamp": ingestion_time,
                        "error_message": str(error),
                    }
                )

                print(f"{table}: error - {error}")

        save_json(
            state,
            CONTAINER,
            STATE_FILE,
        )

    finally:
        connection.close()

    log_name = (
        f"_logs/{partition}/"
        f"ingestion_log_{run_id}.parquet"
    )

    upload_parquet(
        pd.DataFrame(logs),
        CONTAINER,
        log_name,
    )

    print("Capa Bronze finalizada.")
    
if __name__ == "__main__":
    run_bronze()