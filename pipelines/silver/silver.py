import hashlib
import pandas as pd

from pipelines.common.utils import TABLES, read_parquet_prefix, upload_parquet
from pipelines.silver.quality_report import save_quality_report

BRONZE = "bronze"
SILVER = "silver"
AUDIT = "ingestion_timestamp source_system batch_id".split()

INTS = """id_proveedor tiempo_repo_dias art_id id_tienda metros_cuadrados
id_miembro id_trans qty_vendida id_snapshot stock_fisico stock_transito
stock_reservado stock_minimo_config stock_maximo_config id_devolucion
id_trans_origen qty_devuelta""".split()

FLOATS = """calificacion_calidad precio_lista peso_kg precio_unitario_venta
descuento_aplicado vr_reembolso""".split()

DATES = """fec_alta fec_apertura fec_registro fec_ultima_compra fec_trans
fec_snapshot fec_devolucion""".split()

UPPER = """pais_origen unid_medida tipo_tienda genero rango_edad canal_pref
tipo_pago canal_venta motivo_cod canal_devolucion estado_devolucion""".split()

OPTIONAL = """genero rango_edad canal_pref tipo_pago motivo_cod
canal_devolucion estado_devolucion""".split()

REQUIRED = {
    "MSTR_PROVEEDORES": "id_proveedor razon_social".split(),
    "MSTR_ARTICULOS": "art_id id_proveedor desc_art precio_lista".split(),
    "MSTR_TIENDAS": "id_tienda nom_tienda".split(),
    "CRM_MIEMBROS": "id_miembro fec_registro".split(),
    "TRANS_VENTAS": """id_trans id_tienda art_id fec_trans qty_vendida
    precio_unitario_venta""".split(),
    "INV_STOCK_DIARIO": """id_snapshot art_id id_tienda fec_snapshot
    stock_fisico""".split(),
    "POST_DEVOLUCIONES": """id_devolucion id_trans_origen fec_devolucion
    qty_devuelta""".split(),
}

RELATIONS = [
    ("MSTR_ARTICULOS", "id_proveedor", "MSTR_PROVEEDORES", "id_proveedor"),
    ("TRANS_VENTAS", "art_id", "MSTR_ARTICULOS", "art_id"),
    ("TRANS_VENTAS", "id_tienda", "MSTR_TIENDAS", "id_tienda"),
    ("TRANS_VENTAS", "id_miembro", "CRM_MIEMBROS", "id_miembro"),
    ("INV_STOCK_DIARIO", "art_id", "MSTR_ARTICULOS", "art_id"),
    ("INV_STOCK_DIARIO", "id_tienda", "MSTR_TIENDAS", "id_tienda"),
    ("POST_DEVOLUCIONES", "id_trans_origen", "TRANS_VENTAS", "id_trans"),
]


def standardize(df):
    df = df.copy()

    for col in df.select_dtypes(include=["object", "string"]):
        df[col] = df[col].astype("string").str.strip().replace("", pd.NA)

    for col in INTS:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    for col in FLOATS:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in DATES:
        if col in df:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    for col in UPPER:
        if col in df:
            df[col] = df[col].str.upper()

    return df


def clean(df, table):
    errors = []
    source_cols = [col for col in df.columns if col not in AUDIT]
    duplicate = df.duplicated(subset=source_cols, keep="last")

    if duplicate.any():
        rejected = df.loc[duplicate].copy()
        rejected["error_reason"] = "Registro duplicado exacto"
        errors.append(rejected)

    df = df.loc[~duplicate].copy()
    invalid = df[REQUIRED[table]].isna().any(axis=1)

    if invalid.any():
        rejected = df.loc[invalid].copy()
        rejected["error_reason"] = "Campos obligatorios nulos o corruptos"
        errors.append(rejected)

    df = df.loc[~invalid].copy()

    for col in OPTIONAL:
        if col in df:
            df[col] = df[col].fillna("NO INFORMADO")

    return df, errors


def validate_relations(data, errors):
    for child, fk, parent, pk in RELATIONS:
        df = data[child]
        invalid = df[fk].notna() & ~df[fk].isin(data[parent][pk].dropna())

        if invalid.any():
            rejected = df.loc[invalid].copy()
            rejected["error_reason"] = f"Referencia inexistente: {fk}"
            errors[child].append(rejected)
            data[child] = df.loc[~invalid].copy()


def mask_members(df):
    if "id_miembro" not in df:
        return df

    df = df.copy()
    df["id_miembro"] = df["id_miembro"].map(
        lambda value: hashlib.sha256(str(int(value)).encode()).hexdigest()
        if pd.notna(value) else pd.NA
    ).astype("string")

    return df


def run_silver():
    now = pd.Timestamp.now(tz="UTC")
    run_id = now.strftime("%Y%m%d_%H%M%S")
    data = {}
    errors = {table: [] for table in TABLES}
    quality = {}

    for table in TABLES:
        df = read_parquet_prefix(BRONZE, f"{table}/")

        if df.empty:
            raise ValueError(f"No hay datos Bronze para {table}")

        total = len(df)
        df = standardize(df)
        nulls = df.isna().mean().mul(100).round(2).to_dict()
        df, rejected = clean(df, table)

        data[table] = df
        errors[table].extend(rejected)
        quality[table] = (total, nulls)

    validate_relations(data, errors)
    data["CRM_MIEMBROS"] = mask_members(data["CRM_MIEMBROS"])
    data["TRANS_VENTAS"] = mask_members(data["TRANS_VENTAS"])

    report_data = []
    all_errors = []

    for table in TABLES:
        rejected = (
            pd.concat(errors[table], ignore_index=True, sort=False)
            if errors[table] else pd.DataFrame()
        )

        upload_parquet(data[table], SILVER, f"{table}/{table.lower()}.parquet")

        if not rejected.empty:
            rejected["table_name"] = table
            rejected["run_id"] = run_id
            rejected["rejected_at"] = now
            all_errors.append(rejected)

        total, nulls = quality[table]
        report_data.append({
            "table": table,
            "total": total,
            "valid": len(data[table]),
            "rejected": len(rejected),
            "null_percentages": nulls,
        })

        print(f"{table}: {len(data[table]):,} válidos | {len(rejected):,} rechazados")

    error_df = (
        pd.concat(all_errors, ignore_index=True, sort=False)
        if all_errors else pd.DataFrame(columns=["table_name", "error_reason"])
    )

    upload_parquet(error_df, SILVER, f"_errors/errors_{run_id}.parquet")
    print(f"Reporte local: {save_quality_report(run_id, report_data)}")
    print("Capa Silver finalizada.")


if __name__ == "__main__":
    run_silver()