from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from faker import Faker

from src.generation_rules import (
    apply_required_nulls,
    generate_age_groups,
    generate_random_dates,
    generate_sale_values,
    generate_sales_times,
)


def generate_proveedores(
    row_count: int,
    reference_data: dict[str, Any],
    rng: np.random.Generator,
    fake: Faker,
) -> pd.DataFrame:
    """Genera la tabla MSTR_PROVEEDORES."""
    return pd.DataFrame(
        {
            "id_proveedor": np.arange(1, row_count + 1),
            "razon_social": [
                f"{fake.company()} {supplier_id:04d}"
                for supplier_id in range(1, row_count + 1)
            ],
            "pais_origen": rng.choice(reference_data["countries"], size=row_count),
            "tiempo_repo_dias": rng.integers(1, 15, size=row_count),
            "calificacion_calidad": np.round(
                rng.uniform(2.5, 5.0, size=row_count), 2
            ),
            "activo": rng.choice(
                [True, False], size=row_count, p=[0.95, 0.05]
            ),
        }
    )


def generate_articulos(
    row_count: int,
    proveedores: pd.DataFrame,
    reference_data: dict[str, Any],
    start_date: pd.Timestamp,
    rng: np.random.Generator,
    fake: Faker,
) -> pd.DataFrame:
    """Genera la tabla MSTR_ARTICULOS."""
    categories = reference_data["categories"]
    selected_categories = [
        categories[index]
        for index in rng.integers(0, len(categories), size=row_count)
    ]
    subcategories = [
        str(rng.choice(category["subcategories"]))
        for category in selected_categories
    ]
    category_lines = [
        f"{subcategory} - Linea {line}"
        for subcategory, line in zip(
            subcategories,
            rng.integers(1, 6, size=row_count),
            strict=True,
        )
    ]

    prices = np.round(
        np.clip(
            rng.lognormal(mean=np.log(200), sigma=1.0, size=row_count),
            10.00,
            5000.00,
        ),
        2,
    )

    fake.unique.clear()

    return pd.DataFrame(
        {
            "art_id": np.arange(1, row_count + 1),
            "cod_barra": [fake.unique.ean13() for _ in range(row_count)],
            "desc_art": [
                f"{subcategory} {fake.word().capitalize()}"
                for subcategory in subcategories
            ],
            "id_categ_n1": [
                str(category["name"]) for category in selected_categories
            ],
            "id_categ_n2": subcategories,
            "id_categ_n3": category_lines,
            "id_proveedor": rng.choice(
                proveedores["id_proveedor"].to_numpy(), size=row_count
            ),
            "precio_lista": prices,
            "peso_kg": np.round(rng.uniform(0.10, 20.00, size=row_count), 2),
            "unid_medida": rng.choice(
                reference_data["units_of_measure"], size=row_count
            ),
            "activo": rng.choice(
                [True, False], size=row_count, p=[0.97, 0.03]
            ),
            "fec_alta": generate_random_dates(
                row_count=row_count,
                start_date=start_date - pd.DateOffset(years=5),
                end_date=start_date - pd.Timedelta(days=1),
                rng=rng,
            ),
        }
    )


def generate_tiendas(
    row_count: int,
    reference_data: dict[str, Any],
    start_date: pd.Timestamp,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Genera la tabla MSTR_TIENDAS."""
    locations = reference_data["locations"]
    selected_locations = [
        locations[index]
        for index in rng.integers(0, len(locations), size=row_count)
    ]

    return pd.DataFrame(
        {
            "id_tienda": np.arange(1, row_count + 1),
            "nom_tienda": [
                f"RetailMax {location['ciudad']} {store_id:03d}"
                for store_id, location in enumerate(selected_locations, start=1)
            ],
            "tipo_tienda": rng.choice(
                reference_data["store_types"], size=row_count
            ),
            "id_ciudad": [
                location["id_ciudad"] for location in selected_locations
            ],
            "id_pais": [location["id_pais"] for location in selected_locations],
            "metros_cuadrados": rng.integers(100, 10001, size=row_count),
            "activo": rng.choice(
                [True, False], size=row_count, p=[0.95, 0.05]
            ),
            "fec_apertura": generate_random_dates(
                row_count=row_count,
                start_date=start_date - pd.DateOffset(years=15),
                end_date=start_date - pd.Timedelta(days=1),
                rng=rng,
            ),
        }
    )


def generate_miembros(
    row_count: int,
    reference_data: dict[str, Any],
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Genera la tabla CRM_MIEMBROS."""
    locations = reference_data["locations"]
    selected_locations = [
        locations[index]
        for index in rng.integers(0, len(locations), size=row_count)
    ]

    registration_dates = generate_random_dates(
        row_count=row_count,
        start_date=start_date - pd.DateOffset(years=4),
        end_date=start_date,
        rng=rng,
    )
    return pd.DataFrame(
        {
            "id_miembro": np.arange(1, row_count + 1),
            "fec_registro": registration_dates,
            "id_ciudad": [
                location["id_ciudad"] for location in selected_locations
            ],
            "genero": rng.choice(reference_data["genders"], size=row_count),
            "rango_edad": generate_age_groups(row_count=row_count, rng=rng),
            "canal_pref": rng.choice(
                reference_data["sales_channels"], size=row_count
            ),
            "activo": rng.choice(
                [True, False], size=row_count, p=[0.92, 0.08]
            ),
            "fec_ultima_compra": generate_random_dates(
                row_count=row_count,
                start_date=start_date,
                end_date=end_date,
                rng=rng,
            ),
        }
    )


def generate_ventas(
    row_count: int,
    miembros: pd.DataFrame,
    tiendas: pd.DataFrame,
    articulos: pd.DataFrame,
    reference_data: dict[str, Any],
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Genera la tabla TRANS_VENTAS."""
    selected_articles = articulos.iloc[
        rng.integers(0, len(articulos), size=row_count)
    ]

    quantities, unit_prices, discounts = generate_sale_values(
        list_prices=selected_articles["precio_lista"].to_numpy(dtype=float),
        rng=rng,
    )

    channels = rng.choice(reference_data["sales_channels"], size=row_count)
    payment_types = np.empty(row_count, dtype=object)

    # Cada canal usa únicamente los medios de pago configurados.
    for channel in np.unique(channels):
        channel_mask = channels == channel
        payment_types[channel_mask] = rng.choice(
            reference_data["payment_types"][str(channel)],
            size=int(channel_mask.sum()),
        )

    return pd.DataFrame(
        {
            "id_trans": np.arange(1, row_count + 1),
            "id_miembro": rng.choice(
                miembros["id_miembro"].to_numpy(), size=row_count
            ),
            "id_tienda": rng.choice(
                tiendas["id_tienda"].to_numpy(), size=row_count
            ),
            "art_id": selected_articles["art_id"].to_numpy(),
            "fec_trans": generate_random_dates(
                row_count=row_count,
                start_date=start_date,
                end_date=end_date,
                rng=rng,
            ),
            "hra_trans": generate_sales_times(row_count=row_count, rng=rng),
            "qty_vendida": quantities,
            "precio_unitario_venta": unit_prices,
            "descuento_aplicado": discounts,
            "tipo_pago": payment_types,
            "canal_venta": channels,
        }
    )


def generate_stock(
    row_count: int,
    articulos: pd.DataFrame,
    tiendas: pd.DataFrame,
    end_date: pd.Timestamp,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Genera una combinación única de cada artículo con cada tienda."""
    expected_rows = len(articulos) * len(tiendas)

    if row_count != expected_rows:
        raise ValueError(
            "El volumen de stock debe ser igual a artículos × tiendas. "
            f"Configurado: {row_count:,}; esperado: {expected_rows:,}."
        )

    minimum_stock = rng.integers(5, 81, size=row_count)
    maximum_stock = minimum_stock + rng.integers(50, 501, size=row_count)
    physical_stock = np.floor(
        rng.random(row_count) * (maximum_stock + 1)
    ).astype(int)
    reserved_stock = np.minimum(
        rng.integers(0, 51, size=row_count), physical_stock
    )

    return pd.DataFrame(
        {
            "id_snapshot": np.arange(1, row_count + 1),
            "art_id": np.repeat(
                articulos["art_id"].to_numpy(), len(tiendas)
            ),
            "id_tienda": np.tile(
                tiendas["id_tienda"].to_numpy(), len(articulos)
            ),
            "fec_snapshot": end_date,
            "stock_fisico": physical_stock,
            "stock_transito": rng.integers(0, 201, size=row_count),
            "stock_reservado": reserved_stock,
            "stock_minimo_config": minimum_stock,
            "stock_maximo_config": maximum_stock,
        }
    )


def generate_devoluciones(
    row_count: int,
    ventas: pd.DataFrame,
    reference_data: dict[str, Any],
    end_date: pd.Timestamp,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Genera POST_DEVOLUCIONES utilizando ventas existentes."""
    selected_sales = ventas.iloc[
        rng.choice(
            len(ventas),
            size=row_count,
            replace=row_count > len(ventas),
        )
    ].reset_index(drop=True)

    sold_quantities = selected_sales["qty_vendida"].to_numpy(dtype=int)
    returned_quantities = (
        np.floor(rng.random(row_count) * sold_quantities).astype(int) + 1
    )
    statuses = rng.choice(reference_data["return_statuses"], size=row_count)

    net_unit_price = (
        sold_quantities
        * selected_sales["precio_unitario_venta"].to_numpy(dtype=float)
        - selected_sales["descuento_aplicado"].to_numpy(dtype=float)
    ) / sold_quantities

    refund = np.round(net_unit_price * returned_quantities, 2)
    return_dates = (
        pd.to_datetime(selected_sales["fec_trans"])
        + pd.to_timedelta(rng.integers(1, 31, size=row_count), unit="D")
    ).clip(upper=end_date)

    return pd.DataFrame(
        {
            "id_devolucion": np.arange(1, row_count + 1),
            "id_trans_origen": selected_sales["id_trans"].to_numpy(),
            "art_id": selected_sales["art_id"].to_numpy(),
            "id_tienda": selected_sales["id_tienda"].to_numpy(),
            "fec_devolucion": return_dates,
            "qty_devuelta": returned_quantities,
            "motivo_cod": rng.choice(
                reference_data["return_reasons"], size=row_count
            ),
            "canal_devolucion": selected_sales["canal_venta"].to_numpy(),
            "estado_devolucion": statuses,
            "vr_reembolso": np.where(statuses == "approved", refund, 0.00),
        }
    )


def generate_source_data(
    config: dict[str, Any],
    reference_data: dict[str, Any],
) -> dict[str, pd.DataFrame]:
    """Genera las siete tablas fuente del escenario RetailMax."""
    volumes = config["tables"]
    start_date = pd.Timestamp(config["date_range"]["start_date"])
    end_date = pd.Timestamp(config["date_range"]["end_date"])
    seed = int(config["project"]["seed"])

    rng = np.random.default_rng(seed)
    Faker.seed(seed)
    fake = Faker(config["project"]["locale"])
    fake.seed_instance(seed)

    proveedores = generate_proveedores(
        volumes["proveedores"], reference_data, rng, fake
    )
    articulos = generate_articulos(
        volumes["articulos"],
        proveedores,
        reference_data,
        start_date,
        rng,
        fake,
    )
    tiendas = generate_tiendas(
        volumes["tiendas"], reference_data, start_date, rng
    )
    miembros = generate_miembros(
        volumes["miembros"], reference_data, start_date, end_date, rng
    )
    ventas = generate_ventas(
        volumes["ventas"],
        miembros,
        tiendas,
        articulos,
        reference_data,
        start_date,
        end_date,
        rng,
    )
    stock = generate_stock(
        volumes["stock"], articulos, tiendas, end_date, rng
    )
    devoluciones = generate_devoluciones(
        volumes["devoluciones"], ventas, reference_data, end_date, rng
    )

    tables = {
        "MSTR_PROVEEDORES": proveedores,
        "MSTR_ARTICULOS": articulos,
        "MSTR_TIENDAS": tiendas,
        "CRM_MIEMBROS": miembros,
        "TRANS_VENTAS": ventas,
        "INV_STOCK_DIARIO": stock,
        "POST_DEVOLUCIONES": devoluciones,
    }

    apply_required_nulls(
        tables=tables,
        percentage=float(config["data_quality"]["null_percentage"]),
        rng=rng,
    )

    return tables