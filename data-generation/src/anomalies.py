from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _affected_rows(
    total_rows: int,
    rate: float,
) -> int:
    """
    Calcula la cantidad de filas afectadas.
    """
    if total_rows == 0 or rate <= 0:
        return 0

    return min(
        total_rows,
        max(1, round(total_rows * rate)),
    )


def inject_out_of_range_sales(
    ventas: pd.DataFrame,
    start_date: pd.Timestamp,
    rate: float,
    rng: np.random.Generator,
) -> int:
    """
    Asigna fechas anteriores al periodo permitido.
    """
    affected = _affected_rows(len(ventas),rate,)

    if affected == 0:
        return 0

    indexes = rng.choice(ventas.index, size=affected, replace=False,)

    ventas.loc[indexes, "fec_trans"] = (start_date
        - pd.to_timedelta( rng.integers(1, 31, size=affected,), unit="D",)
    ).to_numpy()

    return affected


def inject_duplicate_sales(
    ventas: pd.DataFrame,
    rate: float,
    rng: np.random.Generator,
) -> int:
    """
    Duplica eventos de venta sin repetir id_trans.
    """
    affected = min(_affected_rows(len(ventas), rate,), len(ventas) // 2,)

    if affected == 0:
        return 0

    indexes = rng.choice(ventas.index, size=affected * 2, replace=False,)

    source_indexes = indexes[:affected]
    target_indexes = indexes[affected:]

    business_columns = ventas.columns.drop(
        "id_trans"
    )

    ventas.loc[
        target_indexes,
        business_columns,
    ] = ventas.loc[
        source_indexes,
        business_columns,
    ].to_numpy()

    return affected


def inject_inconsistent_returns(
    devoluciones: pd.DataFrame,
    ventas: pd.DataFrame,
    rate: float,
    rng: np.random.Generator,
) -> int:
    """
    Genera devoluciones con cantidad y reembolso
    superiores a la venta original.
    """
    affected = _affected_rows(
        len(devoluciones),
        rate,
    )

    if affected == 0:
        return 0

    indexes = rng.choice(
        devoluciones.index,
        size=affected,
        replace=False,
    )

    transaction_ids = devoluciones.loc[
        indexes,
        "id_trans_origen",
    ].astype(int)

    selected_sales = (
        ventas.set_index("id_trans")
        .loc[transaction_ids]
    )

    sold_quantities = selected_sales[
        "qty_vendida"
    ].to_numpy(dtype=int)

    net_values = (
        sold_quantities
        * selected_sales[
            "precio_unitario_venta"
        ].to_numpy(dtype=float)
        - selected_sales[
            "descuento_aplicado"
        ].to_numpy(dtype=float)
    )

    devoluciones.loc[
        indexes,
        "estado_devolucion",
    ] = "approved"

    devoluciones.loc[
        indexes,
        "qty_devuelta",
    ] = (
        sold_quantities
        + rng.integers(
            1,
            4,
            size=affected,
        )
    )

    devoluciones.loc[
        indexes,
        "vr_reembolso",
    ] = np.round(
        net_values
        * rng.uniform(
            1.05,
            1.30,
            size=affected,
        ),
        2,
    )

    return affected


def inject_anomalies(
    tables: dict[str, pd.DataFrame],
    config: dict[str, Any],
) -> tuple[
    dict[str, pd.DataFrame],
    pd.DataFrame,
]:
    """
    Introduce los tres patrones de anomalías.
    """
    anomaly_config = config["anomalies"]

    if not anomaly_config["enabled"]:
        empty_report = pd.DataFrame(
            columns=[
                "pattern_name",
                "table_name",
                "affected_rows",
            ]
        )

        return tables, empty_report

    rng = np.random.default_rng(
        int(config["project"]["seed"]) + 1
    )

    ventas = tables["TRANS_VENTAS"]
    devoluciones = tables[
        "POST_DEVOLUCIONES"
    ]

    # Se aplican primero las fechas y después
    # los duplicados para no romper los pares duplicados.
    out_of_range_count = (
        inject_out_of_range_sales(
            ventas=ventas,
            start_date=pd.Timestamp(
                config["date_range"][
                    "start_date"
                ]
            ),
            rate=float(
                anomaly_config[
                    "out_of_range_dates_rate"
                ]
            ),
            rng=rng,
        )
    )

    duplicate_count = inject_duplicate_sales(
        ventas=ventas,
        rate=float(
            anomaly_config[
                "duplicate_sales_rate"
            ]
        ),
        rng=rng,
    )

    inconsistent_count = (
        inject_inconsistent_returns(
            devoluciones=devoluciones,
            ventas=ventas,
            rate=float(
                anomaly_config[
                    "inconsistent_returns_rate"
                ]
            ),
            rng=rng,
        )
    )

    report = pd.DataFrame(
        [
            {
                "pattern_name": "duplicate_sales",
                "table_name": "TRANS_VENTAS",
                "affected_rows": duplicate_count,
            },
            {
                "pattern_name": "out_of_range_dates",
                "table_name": "TRANS_VENTAS",
                "affected_rows": out_of_range_count,
            },
            {
                "pattern_name": "inconsistent_returns",
                "table_name": "POST_DEVOLUCIONES",
                "affected_rows": inconsistent_count,
            },
        ]
    )

    return tables, report