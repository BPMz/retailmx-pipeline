from __future__ import annotations

import numpy as np
import pandas as pd

# Este script solo contiene las reglas de generación de datos.

def generate_random_dates(
    row_count: int,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    rng: np.random.Generator,
) -> pd.DatetimeIndex:
    """
    Genera fechas uniformemente distribuidas
    dentro del periodo configurado.
    """
    total_days = (
        end_date - start_date
    ).days

    offsets = rng.integers(
        0,
        total_days + 1,
        size=row_count,
    )

    return pd.DatetimeIndex(
        start_date
        + pd.to_timedelta(
            offsets,
            unit="D",
        )
    )


def generate_sales_times(
    row_count: int,
    rng: np.random.Generator,
) -> list[str]:
    """
    Genera ventas con mayor concentración
    al mediodía y al final de la tarde.
    """
    hours = [
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
    ]

    probabilities = [
        0.05,
        0.07,
        0.13,
        0.12,
        0.08,
        0.07,
        0.08,
        0.11,
        0.13,
        0.10,
        0.06,
    ]

    selected_hours = rng.choice(
        hours,
        size=row_count,
        p=probabilities,
    )

    minutes = rng.integers(
        0,
        60,
        size=row_count,
    )

    return [
        f"{hour:02d}:{minute:02d}:00"
        for hour, minute in zip(
            selected_hours,
            minutes,
            strict=True,
        )
    ]


def generate_age_groups(
    row_count: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Genera edades con distribución normal
    y las convierte a rangos.
    """
    ages = rng.normal(
        loc=38,
        scale=13,
        size=row_count,
    )

    ages = np.clip(
        np.rint(ages),
        18,
        80,
    ).astype(int)

    return np.select(
        [
            ages <= 25,
            ages <= 35,
            ages <= 45,
            ages <= 60,
        ],
        [
            "18-25",
            "26-35",
            "36-45",
            "46-60",
        ],
        default="+60",
    )


def generate_sale_values(
    list_prices: np.ndarray,
    rng: np.random.Generator,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    """
    Genera cantidades, precios de venta
    y descuentos realistas.
    """
    row_count = len(list_prices)

    quantities = rng.choice(
        [1, 2, 3, 4, 5],
        size=row_count,
        p=[
            0.50,
            0.27,
            0.13,
            0.07,
            0.03,
        ],
    )

    unit_prices = np.round(
        list_prices
        * rng.uniform(
            0.90,
            1.00,
            size=row_count,
        ),
        2,
    )

    discount_rates = rng.choice(
        [
            0.00,
            0.05,
            0.10,
            0.15,
        ],
        size=row_count,
        p=[
            0.55,
            0.20,
            0.15,
            0.10,
        ],
    )

    discounts = np.round(
        quantities
        * unit_prices
        * discount_rates,
        2,
    )

    return (
        quantities,
        unit_prices,
        discounts,
    )


def inject_nulls(
    dataframe: pd.DataFrame,
    column_name: str,
    percentage: float,
    rng: np.random.Generator,
) -> None:
    """
    Introduce nulos intencionales
    en una columna no crítica.
    """
    null_count = int(
        round(
            len(dataframe)
            * percentage
        )
    )

    if null_count <= 0:
        return

    selected_indexes = rng.choice(
        dataframe.index.to_numpy(),
        size=null_count,
        replace=False,
    )

    column = dataframe[column_name]

    if pd.api.types.is_integer_dtype(
        column.dtype
    ):
        dataframe[column_name] = (
            column.astype("Int64")
        )

    dataframe.loc[
        selected_indexes,
        column_name,
    ] = pd.NA


def apply_required_nulls(
    tables: dict[str, pd.DataFrame],
    percentage: float,
    rng: np.random.Generator,
) -> None:
    """
    Aplica el porcentaje configurado de nulos
    únicamente a campos no críticos.
    """
    nullable_columns = {
        "MSTR_ARTICULOS": [
            "peso_kg",
        ],
        "MSTR_TIENDAS": [
            "metros_cuadrados",
        ],
        "CRM_MIEMBROS": [
            "genero",
            "rango_edad",
            "canal_pref",
            "fec_ultima_compra",
        ],
        "TRANS_VENTAS": [
            "id_miembro",
        ],
        "POST_DEVOLUCIONES": [
            "motivo_cod",
        ],
    }

    for table_name, columns in (
        nullable_columns.items()
    ):
        dataframe = tables[table_name]

        for column_name in columns:
            inject_nulls(
                dataframe=dataframe,
                column_name=column_name,
                percentage=percentage,
                rng=rng,
            )


def _run_self_test() -> None:
    """
    Ejecuta una prueba básica del módulo.
    """
    rng = np.random.default_rng(42)

    dates = generate_random_dates(
        row_count=100,
        start_date=pd.Timestamp(
            "2024-06-01"
        ),
        end_date=pd.Timestamp(
            "2025-06-30"
        ),
        rng=rng,
    )

    times = generate_sales_times(
        row_count=100,
        rng=rng,
    )

    age_groups = generate_age_groups(
        row_count=100,
        rng=rng,
    )

    list_prices = np.full(
        100,
        100.00,
    )

    quantities, prices, discounts = (
        generate_sale_values(
            list_prices=list_prices,
            rng=rng,
        )
    )

    test_dataframe = pd.DataFrame(
        {
            "id_miembro": np.arange(
                1,
                101,
            )
        }
    )

    inject_nulls(
        dataframe=test_dataframe,
        column_name="id_miembro",
        percentage=0.05,
        rng=rng,
    )

    assert len(dates) == 100
    assert len(times) == 100
    assert len(age_groups) == 100
    assert len(quantities) == 100
    assert len(prices) == 100
    assert len(discounts) == 100

    assert dates.min() >= pd.Timestamp(
        "2024-06-01"
    )

    assert dates.max() <= pd.Timestamp(
        "2025-06-30"
    )

    assert np.all(
        prices <= list_prices
    )

    assert np.all(
        prices >= list_prices * 0.90
    )

    assert (
        test_dataframe[
            "id_miembro"
        ].isna().sum()
        == 5
    )

    print(
        "Fechas generadas:",
        len(dates),
    )

    print(
        "Horas generadas:",
        len(times),
    )

    print(
        "Rangos de edad generados:",
        len(age_groups),
    )

    print(
        "Valores de venta generados:",
        len(prices),
    )

    print(
        "Nulos introducidos:",
        test_dataframe[
            "id_miembro"
        ].isna().sum(),
    )

    print(
        "\nPrueba de generation_rules.py "
        "completada correctamente."
    )


if __name__ == "__main__":
    _run_self_test()