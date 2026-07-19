import pandas as pd

from pipelines.common.utils import read_parquet_prefix, upload_parquet


SILVER = "silver"
GOLD = "gold"
AUDIT = ["ingestion_timestamp", "source_system", "batch_id"]

COUNTRIES = {
    "CO": "COLOMBIA",
    "MX": "MEXICO",
    "CL": "CHILE",
    "PE": "PERU",
    "EC": "ECUADOR",
}

CITIES = {
    "CO-BOG": "BOGOTA",
    "CO-MDE": "MEDELLIN",
    "CO-CLO": "CALI",
    "MX-CMX": "CIUDAD DE MEXICO",
    "MX-MTY": "MONTERREY",
    "MX-GDL": "GUADALAJARA",
    "CL-SCL": "SANTIAGO",
    "CL-VAP": "VALPARAISO",
    "PE-LIM": "LIMA",
    "PE-AQP": "AREQUIPA",
    "EC-UIO": "QUITO",
    "EC-GYE": "GUAYAQUIL",
}

ZONES = {
    "MX": "NORTE",
    "CO": "CENTRO",
    "EC": "CENTRO",
    "PE": "SUR",
    "CL": "SUR",
}

STORE_TYPES = {
    "HYPERMARKET": "HIPERMERCADO",
    "HIPERMERCADO": "HIPERMERCADO",
    "SUPERMARKET": "SUPERMERCADO",
    "SUPERMERCADO": "SUPERMERCADO",
    "CONVENIENCE_STORE": "CONVENIENCIA",
    "CONVENIENCIA": "CONVENIENCIA",
    "ECOMMERCE": "ECOMMERCE",
}

AGE_ORDER = {
    "18-25": 1,
    "26-35": 2,
    "36-45": 3,
    "46-60": 4,
    "+60": 5,
    "60+": 5,
}

AGE_LABELS = {
    1: "18-25",
    2: "26-35",
    3: "36-45",
    4: "46-60",
    5: "+60",
}


def read_silver(table):
    """Lee una tabla Silver y elimina columnas de auditoría."""
    dataframe = read_parquet_prefix(SILVER, f"{table}/")

    if dataframe.empty:
        raise ValueError(f"No hay datos Silver para {table}")

    return dataframe.drop(columns=AUDIT, errors="ignore")


def save_gold(dataframe, table):
    """Guarda una tabla en Gold."""
    upload_parquet(
        dataframe,
        GOLD,
        f"{table}/{table}.parquet",
    )
    print(f"{table}: {len(dataframe):,} registros")


def create_dim_productos(articles, providers):
    """Une artículos y proveedores."""
    provider_columns = [
        "id_proveedor",
        "razon_social",
        "pais_origen",
        "tiempo_repo_dias",
        "calificacion_calidad",
    ]

    dimension = articles.merge(
        providers[provider_columns],
        on="id_proveedor",
        how="left",
    )

    # La fuente no tiene costo. Se estima un margen
    # simple del 30% sobre el precio de lista.
    dimension["margen_estimado"] = (
        dimension["precio_lista"] * 0.30
    ).round(2)

    dimension["margen_estimado_categoria"] = (
        dimension.groupby("id_categ_n1")["margen_estimado"]
        .transform("mean")
        .round(2)
    )

    return dimension


def create_dim_tiendas(stores):
    """Estandariza tienda, ciudad, país y zona."""
    dimension = stores.copy()

    store_type = (
        dimension["tipo_tienda"]
        .astype("string")
        .str.upper()
        .str.strip()
    )

    dimension["tipo_tienda"] = (
        store_type.map(STORE_TYPES).fillna(store_type)
    )

    dimension["ciudad"] = (
        dimension["id_ciudad"]
        .map(CITIES)
        .fillna(dimension["id_ciudad"])
    )

    dimension["pais"] = (
        dimension["id_pais"]
        .map(COUNTRIES)
        .fillna(dimension["id_pais"])
    )

    dimension["zona_distribucion"] = (
        dimension["id_pais"]
        .map(ZONES)
        .fillna("NO INFORMADO")
    )

    return dimension


def impute_age(customers):
    """Imputa rango de edad con la mediana del canal."""
    result = customers.copy()

    normalized_age = (
        result["rango_edad"]
        .astype("string")
        .str.upper()
        .str.strip()
    )

    age_number = normalized_age.map(AGE_ORDER)

    channel_median = (
        pd.DataFrame({
            "canal_pref": result["canal_pref"],
            "edad_numero": age_number,
        })
        .dropna(subset=["edad_numero"])
        .groupby("canal_pref")["edad_numero"]
        .median()
        .round()
    )

    missing = age_number.isna()

    result.loc[~missing, "rango_edad"] = (
        age_number.loc[~missing].map(AGE_LABELS)
    )

    result.loc[missing, "rango_edad"] = (
        result.loc[missing, "canal_pref"]
        .map(channel_median)
        .map(AGE_LABELS)
        .fillna("NO INFORMADO")
    )

    return result


def create_dim_clientes(customers, cutoff_date):
    """Calcula antigüedad y estandariza cliente."""
    dimension = customers.copy()

    dimension["antiguedad_dias"] = (
        cutoff_date - dimension["fec_registro"]
    ).dt.days.clip(lower=0)

    gender = (
        dimension["genero"]
        .astype("string")
        .str.upper()
        .str.strip()
    )

    gender = gender.replace({
        "MASCULINO": "M",
        "HOMBRE": "M",
        "FEMENINO": "F",
        "MUJER": "F",
    })

    dimension["genero"] = gender.where(
        gender.isin(["M", "F"]),
        "NO INFORMADO",
    )

    return impute_age(dimension)


def create_fact_ventas(sales):
    """Calcula venta neta y banderas de venta."""
    fact = sales.copy()

    fact["descuento_aplicado"] = (
        fact["descuento_aplicado"].fillna(0)
    )

    fact["vr_venta_bruta"] = (
        fact["qty_vendida"]
        * fact["precio_unitario_venta"]
    ).round(2)

    fact["vr_venta_neto"] = (
        fact["vr_venta_bruta"]
        - fact["descuento_aplicado"]
    ).round(2)

    fact["cliente_anonimo"] = fact["id_miembro"].isna()
    fact["id_miembro"] = fact["id_miembro"].fillna(
        "CLIENTE_ANONIMO"
    )

    fact["indicador_descuento"] = (
        fact["descuento_aplicado"] > 0
    )

    return fact


def create_fact_inventario(stock, sales):
    """Calcula cobertura y alerta de quiebre."""
    fact = stock.copy()
    sales = sales.copy()

    fact["fec_snapshot"] = (
        pd.to_datetime(fact["fec_snapshot"])
        .dt.normalize()
    )

    sales["fec_trans"] = (
        pd.to_datetime(sales["fec_trans"])
        .dt.normalize()
    )

    averages = []

    for snapshot_date in fact["fec_snapshot"].dropna().unique():
        snapshot_date = pd.Timestamp(snapshot_date)
        start_date = snapshot_date - pd.Timedelta(days=13)

        recent_sales = sales[
            sales["fec_trans"].between(start_date, snapshot_date)
        ]

        average = (
            recent_sales.groupby(
                ["art_id", "id_tienda"],
                as_index=False,
            )["qty_vendida"]
            .sum()
        )

        average["promedio_ventas_14_dias"] = (
            average["qty_vendida"] / 14
        ).round(2)

        average["fec_snapshot"] = snapshot_date

        averages.append(
            average[
                [
                    "art_id",
                    "id_tienda",
                    "fec_snapshot",
                    "promedio_ventas_14_dias",
                ]
            ]
        )

    if averages:
        average_sales = pd.concat(averages, ignore_index=True)

        fact = fact.merge(
            average_sales,
            on=["art_id", "id_tienda", "fec_snapshot"],
            how="left",
        )
    else:
        fact["promedio_ventas_14_dias"] = 0

    fact["promedio_ventas_14_dias"] = (
        fact["promedio_ventas_14_dias"].fillna(0)
    )

    fact["cobertura_dias"] = (
        fact["stock_fisico"]
        / fact["promedio_ventas_14_dias"]
    ).where(
        fact["promedio_ventas_14_dias"] > 0
    ).round(2)

    fact["alerta_quiebre"] = (
        (fact["promedio_ventas_14_dias"] > 0)
        & (fact["cobertura_dias"] < 7)
    )

    fact["diferencia_stock_minimo"] = (
        fact["stock_fisico"]
        - fact["stock_minimo_config"]
    )

    return fact


def create_fact_devoluciones(returns, sales):
    """Une devoluciones con la venta original."""
    sale_columns = [
        "id_trans",
        "fec_trans",
        "precio_unitario_venta",
        "canal_venta",
    ]

    fact = returns.merge(
        sales[sale_columns],
        left_on="id_trans_origen",
        right_on="id_trans",
        how="left",
    )

    fact["precio_original"] = fact["precio_unitario_venta"]

    fact["vr_devolucion"] = (
        fact["qty_devuelta"]
        * fact["precio_original"]
    ).round(2)

    fact["motivo_descripcion"] = (
        fact["motivo_cod"]
        .astype("string")
        .str.replace("_", " ", regex=False)
        .str.title()
    )

    fact["estado_devolucion"] = (
        fact["estado_devolucion"]
        .astype("string")
        .str.replace("_", " ", regex=False)
        .str.title()
    )

    return fact.drop(columns=["id_trans"])


def create_fact_rfm_clientes(sales, customers):
    """Calcula RFM sobre 90 días para clientes activos."""
    identified = sales[
        sales["id_miembro"] != "CLIENTE_ANONIMO"
    ].copy()

    cutoff_date = identified["fec_trans"].max()
    start_180 = cutoff_date - pd.Timedelta(days=179)
    start_90 = cutoff_date - pd.Timedelta(days=89)

    active = (
        identified[identified["fec_trans"] >= start_180]
        [["id_miembro"]]
        .drop_duplicates()
    )

    recent = identified[
        identified["fec_trans"] >= start_90
    ]

    rfm = (
        recent.groupby("id_miembro", as_index=False)
        .agg(
            ultima_compra=("fec_trans", "max"),
            frecuencia=("id_trans", "nunique"),
            monto=("vr_venta_neto", "sum"),
        )
    )

    fact = active.merge(rfm, on="id_miembro", how="left")

    fact["recencia_dias"] = (
        cutoff_date - fact["ultima_compra"]
    ).dt.days.fillna(91)

    fact["frecuencia"] = fact["frecuencia"].fillna(0)
    fact["monto"] = fact["monto"].fillna(0).round(2)

    fact["score_r"] = pd.qcut(
        fact["recencia_dias"].rank(method="first"),
        5,
        labels=[5, 4, 3, 2, 1],
    ).astype(int)

    fact["score_f"] = pd.qcut(
        fact["frecuencia"].rank(method="first"),
        5,
        labels=[1, 2, 3, 4, 5],
    ).astype(int)

    fact["score_m"] = pd.qcut(
        fact["monto"].rank(method="first"),
        5,
        labels=[1, 2, 3, 4, 5],
    ).astype(int)

    fact["score_rfm"] = (
        "R" + fact["score_r"].astype(str)
        + "-F" + fact["score_f"].astype(str)
        + "-M" + fact["score_m"].astype(str)
    )

    champions = (
        (fact["score_r"] >= 4)
        & (fact["score_f"] >= 4)
        & (fact["score_m"] >= 4)
    )

    fact["segmento_rfm"] = fact["score_rfm"]
    fact["nombre_segmento"] = "SIN CLASIFICAR"
    fact.loc[champions, "nombre_segmento"] = "CHAMPIONS"

    customer_columns = [
        "id_miembro",
        "canal_pref",
        "genero",
        "rango_edad",
    ]

    fact = fact.merge(
        customers[customer_columns],
        on="id_miembro",
        how="left",
    )

    fact["fecha_corte"] = cutoff_date

    return fact


def run_gold():
    """Ejecuta la capa Gold."""
    providers = read_silver("MSTR_PROVEEDORES")
    articles = read_silver("MSTR_ARTICULOS")
    stores = read_silver("MSTR_TIENDAS")
    customers = read_silver("CRM_MIEMBROS")
    sales = read_silver("TRANS_VENTAS")
    stock = read_silver("INV_STOCK_DIARIO")
    returns = read_silver("POST_DEVOLUCIONES")

    cutoff_date = sales["fec_trans"].max()

    dim_productos = create_dim_productos(articles, providers)
    dim_tiendas = create_dim_tiendas(stores)
    dim_clientes = create_dim_clientes(customers, cutoff_date)
    fact_ventas = create_fact_ventas(sales)
    fact_inventario = create_fact_inventario(stock, fact_ventas)
    fact_devoluciones = create_fact_devoluciones(
        returns,
        fact_ventas,
    )
    fact_rfm_clientes = create_fact_rfm_clientes(
        fact_ventas,
        dim_clientes,
    )

    save_gold(dim_productos, "dim_productos")
    save_gold(dim_tiendas, "dim_tiendas")
    save_gold(dim_clientes, "dim_clientes")
    save_gold(fact_ventas, "fact_ventas")
    save_gold(fact_inventario, "fact_inventario")
    save_gold(fact_devoluciones, "fact_devoluciones")
    save_gold(fact_rfm_clientes, "fact_rfm_clientes")

    print("Capa Gold finalizada.")


if __name__ == "__main__":
    run_gold()