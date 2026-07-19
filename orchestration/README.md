## Comando para ejecucion del orquestador pipeline
python -m orchestration.run_pipeline

## Resultado de la ejecución

La ejecución completa del pipeline finalizó correctamente:

- Bronze: 23,595 registros ingeridos desde Azure SQL.
- Silver: 23,595 registros válidos.
- Gold:
  - 500 productos.
  - 15 tiendas.
  - 5,000 clientes.
  - 10,000 ventas.
  - 7,500 registros de inventario.
  - 500 devoluciones.
  - 2,873 clientes segmentados mediante RFM.
- Estado general: Exitoso.