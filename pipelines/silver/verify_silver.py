from pipelines.common.utils import read_parquet_prefix


bronze = read_parquet_prefix(
    "bronze",
    "CRM_MIEMBROS/",
)

silver = read_parquet_prefix(
    "silver",
    "CRM_MIEMBROS/",
)

print("TIPOS EN BRONZE")
print(bronze.dtypes)

print("\nTIPOS EN SILVER")
print(silver.dtypes)

print("\nID EN BRONZE")
print(bronze["id_miembro"].head())

print("\nID EN SILVER")
print(silver["id_miembro"].head())

print("\nGÉNERO EN BRONZE")
print(bronze["genero"].head(10))

print("\nGÉNERO EN SILVER")
print(silver["genero"].head(10))

print(
    "\nValores NO INFORMADO:",
    (silver["genero"] == "NO INFORMADO").sum(),
)

bronze_ventas = read_parquet_prefix(
    "bronze",
    "TRANS_VENTAS/",
)

silver_ventas = read_parquet_prefix(
    "silver",
    "TRANS_VENTAS/",
)

columns = [
    "id_trans",
    "fec_trans",
    "qty_vendida",
    "precio_unitario_venta",
    "id_miembro",
]

print("\nBRONZE")
print(bronze_ventas[columns].dtypes)

print("\nSILVER")
print(silver_ventas[columns].dtypes)