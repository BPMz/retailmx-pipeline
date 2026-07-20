# RetailMax - Reporte de calidad Silver

## Tabla: MSTR_PROVEEDORES
- Registros totales: 80
- Registros rechazados: 0
- Registros conformes: 80
- Porcentaje conforme: 100.00%
### Porcentaje de nulos por columna
- `id_proveedor`: 0.00%
- `razon_social`: 0.00%
- `pais_origen`: 0.00%
- `tiempo_repo_dias`: 0.00%
- `calificacion_calidad`: 0.00%
- `activo`: 0.00%
- `ingestion_timestamp`: 0.00%
- `source_system`: 0.00%
- `batch_id`: 0.00%

## Tabla: MSTR_ARTICULOS
- Registros totales: 500
- Registros rechazados: 0
- Registros conformes: 500
- Porcentaje conforme: 100.00%
### Porcentaje de nulos por columna
- `art_id`: 0.00%
- `cod_barra`: 0.00%
- `desc_art`: 0.00%
- `id_categ_n1`: 0.00%
- `id_categ_n2`: 0.00%
- `id_categ_n3`: 0.00%
- `id_proveedor`: 0.00%
- `precio_lista`: 0.00%
- `peso_kg`: 5.00%
- `unid_medida`: 0.00%
- `activo`: 0.00%
- `fec_alta`: 0.00%
- `ingestion_timestamp`: 0.00%
- `source_system`: 0.00%
- `batch_id`: 0.00%

## Tabla: MSTR_TIENDAS
- Registros totales: 15
- Registros rechazados: 0
- Registros conformes: 15
- Porcentaje conforme: 100.00%
### Porcentaje de nulos por columna
- `id_tienda`: 0.00%
- `nom_tienda`: 0.00%
- `tipo_tienda`: 0.00%
- `id_ciudad`: 0.00%
- `id_pais`: 0.00%
- `metros_cuadrados`: 6.67%
- `activo`: 0.00%
- `fec_apertura`: 0.00%
- `ingestion_timestamp`: 0.00%
- `source_system`: 0.00%
- `batch_id`: 0.00%

## Tabla: CRM_MIEMBROS
- Registros totales: 5,000
- Registros rechazados: 0
- Registros conformes: 5,000
- Porcentaje conforme: 100.00%
### Porcentaje de nulos por columna
- `id_miembro`: 0.00%
- `fec_registro`: 0.00%
- `id_ciudad`: 0.00%
- `genero`: 5.00%
- `rango_edad`: 5.00%
- `canal_pref`: 5.00%
- `activo`: 0.00%
- `fec_ultima_compra`: 5.00%
- `ingestion_timestamp`: 0.00%
- `source_system`: 0.00%
- `batch_id`: 0.00%

## Tabla: TRANS_VENTAS
- Registros totales: 10,000
- Registros rechazados: 0
- Registros conformes: 10,000
- Porcentaje conforme: 100.00%
### Porcentaje de nulos por columna
- `id_trans`: 0.00%
- `id_miembro`: 5.00%
- `id_tienda`: 0.00%
- `art_id`: 0.00%
- `fec_trans`: 0.00%
- `hra_trans`: 0.00%
- `qty_vendida`: 0.00%
- `precio_unitario_venta`: 0.00%
- `descuento_aplicado`: 0.00%
- `tipo_pago`: 0.00%
- `canal_venta`: 0.00%
- `ingestion_timestamp`: 0.00%
- `source_system`: 0.00%
- `batch_id`: 0.00%

## Tabla: INV_STOCK_DIARIO
- Registros totales: 7,500
- Registros rechazados: 0
- Registros conformes: 7,500
- Porcentaje conforme: 100.00%
### Porcentaje de nulos por columna
- `id_snapshot`: 0.00%
- `art_id`: 0.00%
- `id_tienda`: 0.00%
- `fec_snapshot`: 0.00%
- `stock_fisico`: 0.00%
- `stock_transito`: 0.00%
- `stock_reservado`: 0.00%
- `stock_minimo_config`: 0.00%
- `stock_maximo_config`: 0.00%
- `ingestion_timestamp`: 0.00%
- `source_system`: 0.00%
- `batch_id`: 0.00%

## Tabla: POST_DEVOLUCIONES
- Registros totales: 500
- Registros rechazados: 0
- Registros conformes: 500
- Porcentaje conforme: 100.00%
### Porcentaje de nulos por columna
- `id_devolucion`: 0.00%
- `id_trans_origen`: 0.00%
- `art_id`: 0.00%
- `id_tienda`: 0.00%
- `fec_devolucion`: 0.00%
- `qty_devuelta`: 0.00%
- `motivo_cod`: 5.00%
- `canal_devolucion`: 0.00%
- `estado_devolucion`: 0.00%
- `vr_reembolso`: 0.00%
- `ingestion_timestamp`: 0.00%
- `source_system`: 0.00%
- `batch_id`: 0.00%
