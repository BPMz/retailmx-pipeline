# RetailMax Medallion Data Pipeline

Proyecto de ingeniería de datos desarrollado a partir de un escenario de **Retail y Comercio Electrónico**.

El objetivo es construir un pipeline end-to-end con arquitectura Medallion, desde la generación de datos sintéticos hasta la creación de un modelo analítico en la capa Gold.

La solución utiliza **Python**, **Azure SQL Database**, **Azure Data Lake Storage Gen2**, **Bicep** y **Azure CLI**. La ejecución de la Fase 4 se realiza actualmente mediante un orquestador local desarrollado en Python.

---

## Sector elegido, plataforma cloud y justificación

## Sector elegido

El sector seleccionado para el desarrollo del proyecto es Retail y Comercio Electrónico.

Este sector fue elegido porque genera grandes cantidades de información relacionada con:

- ventas;
- clientes;
- productos;
- proveedores;
- tiendas;
- inventario;
- devoluciones.

La integración de estas fuentes permite representar problemas comunes de ingeniería de datos, como la limpieza de información, la validación de relaciones entre tablas, la identificación de productos con bajo inventario, el análisis de ventas y la segmentación de clientes.

El escenario también permite construir un modelo analítico compuesto por dimensiones y tablas de hechos, facilitando el análisis por producto, tienda, cliente, canal, proveedor y periodo.

## Plataforma cloud seleccionada

La plataforma seleccionada es Microsoft Azure.

Los principales servicios utilizados son:

- Azure SQL Database como fuente relacional;
- Azure Data Lake Storage Gen2 para almacenar las capas Bronze, Silver y Gold;
- Azure Key Vault como recurso de infraestructura para la administración de secretos;
- Log Analytics Workspace como base para monitoreo;
- Azure Monitor Action Group como base para alertas;
- Bicep para definir la infraestructura como código;
- Azure CLI para validar y desplegar los recursos.

## Justificación de Azure

Azure fue seleccionado porque permite integrar una fuente SQL con almacenamiento de datos en la nube y recursos de seguridad y monitoreo dentro del mismo ecosistema.

Azure SQL Database permite representar la base de datos transaccional de RetailMax, mientras que Azure Data Lake Storage Gen2 permite organizar los datos mediante una arquitectura Medallion.

Bicep y Azure CLI permiten que la infraestructura sea reproducible, parametrizada y desplegable sin crear manualmente cada recurso desde el portal.

La selección también permite demostrar conocimientos de:

bases de datos relacionales en la nube;
almacenamiento de archivos Parquet;
arquitectura Medallion;
infraestructura como código;
seguridad mediante variables de entorno;
procesamiento incremental;
integración entre Python y servicios cloud.

---

## 1. Descripción general

El proyecto simula el flujo de información de una empresa retail llamada **RetailMax**.

Los datos representan las principales operaciones de la compañía:

- proveedores;
- artículos;
- tiendas;
- clientes;
- ventas;
- inventario;
- devoluciones.

El flujo implementado incluye:

1. Generación de datos sintéticos.
2. Exportación de los datos en CSV y Parquet.
3. Carga de los archivos CSV hacia Azure SQL Database.
4. Ingesta desde Azure SQL hacia la capa Bronze en ADLS Gen2.
5. Limpieza, validación y tratamiento de errores en la capa Silver.
6. Construcción del modelo analítico en la capa Gold.
7. Ejecución secuencial de Bronze, Silver y Gold mediante un orquestador local.
8. Generación de documentación y evidencias de ejecución.

---

## 2. Arquitectura general

El proyecto utiliza una arquitectura Medallion:

```text
Configuración YAML
        |
        v
Generación de datos sintéticos
        |
        v
Archivos CSV y Parquet locales
        |
        v
Azure SQL Database
        |
        v
Bronze - Datos crudos en ADLS Gen2
        |
        v
Silver - Datos limpios y validados
        |
        v
Gold - Modelo analítico
```

Cada capa tiene una responsabilidad específica:

- **Bronze:** conserva los datos de origen y agrega metadatos técnicos.
- **Silver:** limpia, estandariza y valida la información.
- **Gold:** construye dimensiones, hechos e indicadores analíticos.

Los datos deben avanzar por las capas en el siguiente orden:

```text
Azure SQL -> Bronze -> Silver -> Gold
```

---

## 3. Tecnologías y plataformas utilizadas

|---|---|
| Python 3.12 | Generación, carga, transformación y orquestación local |
| Pandas | Limpieza, validación y transformación de datos |
| NumPy | Generación de valores y distribuciones |
| Faker | Generación de datos sintéticos |
| PyArrow | Lectura y escritura de archivos Parquet |
| YAML | Configuración de volúmenes, fechas y reglas |
| pyodbc y Microsoft ODBC Driver 18 | Conexión de Python con Azure SQL Database |
| python-dotenv | Lectura de variables de entorno |
| Azure SQL Database | Fuente relacional del pipeline |
| Azure Data Lake Storage Gen2 | Almacenamiento de las capas Bronze, Silver y Gold |
| Azure Storage SDK para Python | Lectura y escritura de archivos en ADLS Gen2 |
| Azure Key Vault | Recurso desplegado para la administración futura de secretos |
| Log Analytics Workspace | Recurso desplegado como base para monitoreo futuro |
| Azure Monitor Action Group | Recurso desplegado como base para alertas futuras |
| Azure Data Factory | Recurso desplegado como base para orquestación futura |
| Bicep | Definición de infraestructura como código |
| Azure CLI | Validación y despliegue de infraestructura |
| Git | Control de versiones |
| GitHub | Repositorio y entrega del proyecto |

---

## 4. Datos fuente

El proyecto trabaja con siete tablas:

| Tabla | Descripción |
|---|---|
| `MSTR_PROVEEDORES` | Catálogo de proveedores |
| `MSTR_ARTICULOS` | Catálogo de productos |
| `MSTR_TIENDAS` | Catálogo de tiendas |
| `CRM_MIEMBROS` | Información de clientes |
| `TRANS_VENTAS` | Transacciones de ventas |
| `INV_STOCK_DIARIO` | Inventario diario |
| `POST_DEVOLUCIONES` | Devoluciones registradas |

Las relaciones principales permiten asociar:

- artículos con proveedores;
- ventas con artículos, tiendas y clientes;
- inventario con artículos y tiendas;
- devoluciones con las ventas correspondientes.

El modelo entidad-relación se encuentra en:

```text
docs/diagrams/
```

---

## 5. Generación de datos sintéticos

La generación se controla mediante archivos YAML.

Archivos principales:

```text
data-generation/config/generation_config.yaml
data-generation/config/reference_data.yaml
```

La configuración permite definir:

- semilla de generación;
- periodo de fechas;
- volumen por tabla;
- porcentaje de valores nulos;
- formatos de salida;
- anomalías intencionales.

La semilla utilizada es:

```text
42
```

Esto permite reproducir los resultados mientras la configuración permanezca igual.

Los datos se exportan en:

- CSV;
- Parquet.

También se agregan anomalías controladas:

- ventas duplicadas;
- fechas fuera del rango esperado;
- devoluciones inconsistentes.

Archivos principales de generación:

```text
data-generation/src/main.py
data-generation/src/generate_data.py
data-generation/src/generation_rules.py
data-generation/src/anomalies.py
data-generation/src/export_data.py
data-generation/src/config.py
```

Las salidas se generan en:

```text
data-generation/output/csv/
data-generation/output/parquet/
```

---

## 6. Volúmenes utilizados

Para demostrar el funcionamiento completo del pipeline se utilizaron volúmenes reducidos.

| Tabla | Registros |
|---|---:|
| `MSTR_PROVEEDORES` | 80 |
| `MSTR_ARTICULOS` | 500 |
| `MSTR_TIENDAS` | 15 |
| `CRM_MIEMBROS` | 5,000 |
| `TRANS_VENTAS` | 10,000 |
| `INV_STOCK_DIARIO` | 7,500 |
| `POST_DEVOLUCIONES` | 500 |
| **Total** | **23,595** |

Los volúmenes pueden modificarse desde el archivo YAML sin cambiar la lógica principal del proyecto.

La reducción permite ejecutar la solución con los recursos disponibles y controlar el consumo de Azure.

---

## 7. Carga hacia Azure SQL Database

Azure SQL Database funciona como la fuente relacional del pipeline.

El script de carga es:

```text
data-generation/src/load_to_azure_sql.py
```

Los scripts SQL relacionados son:

```text
data-generation/sql/create_source_tables.sql
data-generation/sql/02_validate_source_tables.sql
```

El proceso general es:

```text
Generar CSV
    -> Crear tablas en Azure SQL
    -> Cargar registros
    -> Validar conteos
```

La carga se valida mediante consultas `SELECT COUNT(*)` sobre las siete tablas.

Las credenciales se obtienen mediante variables de entorno y no se almacenan directamente en el código.

---

## 8. Capa Bronze

La capa Bronze ingesta los datos desde Azure SQL Database hacia Azure Data Lake Storage Gen2.

Archivo principal:

```text
pipelines/bronze/bronze.py
```

La capa realiza las siguientes acciones:

- consulta las tablas de Azure SQL;
- conserva el esquema original;
- agrega columnas de auditoría;
- escribe archivos Parquet;
- particiona los datos por fecha;
- registra la cantidad de filas procesadas;
- utiliza Change Tracking para cargas posteriores.

Columnas de auditoría:

```text
ingestion_timestamp
source_system
batch_id
```

Estructura de particionamiento:

```text
bronze/<tabla>/year=YYYY/month=MM/day=DD/
```

La primera ejecución procesa la información inicial. Las ejecuciones posteriores consultan registros nuevos o modificados.

Cuando no existen cambios, Bronze puede finalizar con cero registros procesados. Este comportamiento es esperado y no representa un error.

Ejecución:

```powershell
python -m pipelines.bronze.bronze
```

---

## 9. Capa Silver

La capa Silver lee los archivos Parquet de Bronze y aplica reglas de calidad.

Archivo principal:

```text
pipelines/silver/silver.py
```

Incluye:

- eliminación de duplicados exactos;
- validación de campos obligatorios;
- conversión de fechas;
- conversión de columnas numéricas;
- limpieza básica de textos;
- estrategia de tratamiento de valores nulos;
- validación de integridad referencial;
- separación de registros rechazados;
- documentación del motivo de rechazo;
- protección de identificadores sensibles;
- generación de un reporte de calidad.

Los registros válidos se almacenan en Silver.

Los registros incorrectos se guardan por separado con su motivo correspondiente.

El reporte de calidad incluye:

- registros recibidos;
- duplicados;
- registros rechazados;
- registros conformes;
- porcentaje de conformidad;
- porcentaje de nulos por columna.

Ejemplo de salida:

```text
MSTR_PROVEEDORES: 80 válidos | 0 rechazados
MSTR_ARTICULOS: 500 válidos | 0 rechazados
MSTR_TIENDAS: 15 válidos | 0 rechazados
CRM_MIEMBROS: 5,000 válidos | 0 rechazados
TRANS_VENTAS: 9,950 válidos | 50 rechazados
INV_STOCK_DIARIO: 7,500 válidos | 0 rechazados
POST_DEVOLUCIONES: 496 válidos | 4 rechazados
```

Los resultados pueden variar dependiendo de las anomalías generadas.

Ejecución:

```powershell
python -m pipelines.silver.silver
```

---

## 10. Capa Gold

La capa Gold construye el modelo analítico final a partir de los datos de Silver.

Archivo principal:

```text
pipelines/gold/gold.py
```

Tablas principales:

| Tabla | Propósito |
|---|---|
| `dim_productos` | Análisis por producto, categoría y proveedor |
| `dim_tiendas` | Análisis por tienda y ubicación |
| `dim_clientes` | Análisis y segmentación de clientes |
| `fact_ventas` | Análisis de ventas, descuentos y canales |
| `fact_inventario` | Seguimiento de stock y riesgo de quiebre |
| `fact_devoluciones` | Análisis de devoluciones |
| `fact_rfm_clientes` | Segmentación RFM de clientes |

### dim_productos

Integra artículos y proveedores.

Incluye información de:

- producto;
- proveedor;
- categoría;
- jerarquía de categorías;
- costo;
- precio;
- margen estimado.

### dim_tiendas

Incluye:

- tienda;
- tipo de tienda;
- ciudad;
- país;
- zona de distribución.

### dim_clientes

Incluye:

- identificador protegido;
- antigüedad;
- rango de edad;
- género estandarizado;
- canal preferido.

### fact_ventas

Incluye:

- fecha;
- tienda;
- producto;
- cliente;
- cantidad;
- venta bruta;
- descuento;
- venta neta;
- canal;
- medio de pago;
- indicador de descuento.

### fact_inventario

Incluye:

- stock físico;
- stock disponible;
- stock reservado;
- stock en tránsito;
- punto de reorden;
- cobertura estimada;
- indicador de bajo stock.

### fact_devoluciones

Incluye:

- venta relacionada;
- artículo;
- tienda;
- motivo;
- estado;
- importe;
- tiempo de aprobación.

### fact_rfm_clientes

Permite segmentar clientes según:

- recencia;
- frecuencia;
- valor monetario.

Ejecución:

```powershell
python -m pipelines.gold.gold
```

---

## 11. Infraestructura como código

La infraestructura se define mediante Bicep.

Archivos principales:

```text
infra/main.bicep
infra/main.dev.bicepparam
infra/main.prod.bicepparam
infra/README.md
```

Los recursos desplegados incluyen:

- Resource Group;
- Storage Account con ADLS Gen2;
- contenedor `bronze`;
- contenedor `silver`;
- contenedor `gold`;
- Azure Key Vault;
- Log Analytics Workspace;
- Azure Monitor Action Group.

Se utilizan parámetros separados para los ambientes:

- desarrollo;
- producción.

La infraestructura se valida y despliega mediante Azure CLI.

---

## 12. Fase 4: orquestación local

La Fase 4 se implementó de forma local mediante un orquestador sencillo en Python.

Archivo principal:

```text
orchestration/run_pipeline.py
```

El orquestador ejecuta las capas en el orden correcto:

```text
Bronze -> Silver -> Gold
```

Sus funciones principales son:

- iniciar la ejecución del pipeline;
- ejecutar cada capa en secuencia;
- evitar que Silver se ejecute antes de Bronze;
- evitar que Gold se ejecute antes de Silver;
- aplicar reintentos básicos;
- detener el proceso cuando una capa falla;
- mostrar el tiempo de ejecución por capa;
- mostrar la duración total;
- presentar un resumen final.

Ejecución:

```powershell
python -m orchestration.run_pipeline
```

La implementación actual permite demostrar la orquestación y el control del flujo desde el entorno local.

Esta solución es provisional. Como mejora futura se planea trasladar la orquestación a **Azure Data Factory**, para ejecutar y monitorear el pipeline desde un servicio administrado en Azure.

Azure Data Factory forma parte únicamente de los próximos pasos y no de la implementación actual.

---

## 13. Calidad de datos

Las validaciones de calidad se aplican principalmente en Silver.

Relaciones verificadas:

```text
MSTR_ARTICULOS.id_proveedor
    -> MSTR_PROVEEDORES.id_proveedor

TRANS_VENTAS.art_id
    -> MSTR_ARTICULOS.art_id

TRANS_VENTAS.id_tienda
    -> MSTR_TIENDAS.id_tienda

TRANS_VENTAS.id_miembro
    -> CRM_MIEMBROS.id_miembro

INV_STOCK_DIARIO.art_id
    -> MSTR_ARTICULOS.art_id

INV_STOCK_DIARIO.id_tienda
    -> MSTR_TIENDAS.id_tienda

POST_DEVOLUCIONES.id_trans
    -> TRANS_VENTAS.id_trans
```

Los registros que no cumplen las reglas se separan y conservan como evidencia.

---

## 14. Seguridad y configuración

La información sensible se configura mediante variables de entorno.

Archivo de referencia:

```text
.env.example
```

Archivo local:

```text
.env
```

El archivo `.env` no se incluye en GitHub.

La configuración permite establecer:

- conexión hacia Azure SQL Database;
- servidor;
- base de datos;
- usuario;
- contraseña;
- conexión hacia Azure Storage.

Se aplican las siguientes reglas:

- no almacenar contraseñas directamente en Python;
- no subir cadenas de conexión;
- excluir `.env` mediante `.gitignore`;
- mantener únicamente valores de ejemplo en `.env.example`.

Azure Key Vault fue desplegado como parte de la infraestructura.

---

## 15. Estructura del proyecto

```text
retail-pipeline/
│
├── data-generation/
│   ├── config/
│   │   ├── generation_config.yaml
│   │   └── reference_data.yaml
│   │
│   ├── output/
│   │   ├── csv/
│   │   └── parquet/
│   │
│   ├── sql/
│   │   ├── create_source_tables.sql
│   │   └── 02_validate_source_tables.sql
│   │
│   └── src/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── generate_data.py
│       ├── generation_rules.py
│       ├── anomalies.py
│       ├── export_data.py
│       └── load_to_azure_sql.py
│
├── pipelines/
│   ├── bronze/
│   │   ├── __init__.py
│   │   └── bronze.py
│   │
│   ├── silver/
│   │   ├── __init__.py
│   │   └── silver.py
│   │   └── quality_report.py
|   |   └── verify_silver.py
|   |
│   ├── gold/
│   │   ├── __init__.py
│   │   └── gold.py
│   │
│   ├── common/
│       ├── __init__.py
│       └── utils.py
│  
│
├── infra/
│   ├── main.bicep
│   ├── main.dev.bicepparam
│   └── main.prod.bicepparam
│  
│
├── orchestration/
│   └── run_pipeline.py
│
|
├── docs/
│   ├── diagrams/
│   ├── evidence/
│   └── 01_fase_1_origen_y_carga.md
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

Responsabilidad de los directorios:

- `data-generation/`: generación y carga de los datos fuente;
- `pipelines/bronze/`: ingesta desde Azure SQL hacia ADLS Gen2;
- `pipelines/silver/`: limpieza, validación y separación de errores;
- `pipelines/gold/`: construcción del modelo analítico;
- `pipelines/common/`: funciones compartidas;
- `orchestration/run_pipeline.py`: orquestador local de la Fase 4;
- `infra/`: infraestructura definida mediante Bicep;
- `orchestration/`: documentación de la orquestación;
- `docs/`: diagramas, documentación y evidencias.


## 16. Cómo ejecutar localmente

### 16.1 Crear el entorno virtual

```powershell
python -m venv .venv
```

### 16.2 Activar el entorno virtual

```powershell
.\.venv\Scripts\Activate.ps1
```

### 16.3 Instalar dependencias

```powershell
python -m pip install -r requirements.txt
```

### 16.4 Configurar variables de entorno

Crear el archivo local:

```powershell
Copy-Item .env.example .env
```

Después se deben completar las variables de Azure SQL y Azure Storage.

### 16.5 Generar los datos

```powershell
cd data-generation
python -m src.main
```

### 16.6 Crear las tablas en Azure SQL

Ejecutar:

```text
data-generation/sql/create_source_tables.sql
```

### 16.7 Cargar los datos hacia Azure SQL

```powershell
python -m src.load_to_azure_sql
```

### 16.8 Regresar a la raíz

```powershell
cd ..
```

### 16.9 Ejecutar el pipeline completo

```powershell
python -m pipelines.run_pipeline
```

También se pueden ejecutar las capas individualmente:

```powershell
python -m pipelines.bronze.bronze
python -m pipelines.silver.silver
python -m pipelines.gold.gold
```

Orden completo:

```text
1. Generar datos.
2. Crear las tablas en Azure SQL.
3. Cargar los datos.
4. Ejecutar Bronze.
5. Ejecutar Silver.
6. Ejecutar Gold.
```

Después de la carga inicial, no es necesario repetir la generación y la carga para cada ejecución del pipeline.

---

## 17. Evidencias principales

Las evidencias se almacenan en:

```text
docs/evidence/
```

Incluyen:

### Fase 1

- ejecución de la generación;
- archivos CSV y Parquet;
- conteos en Azure SQL;
- modelo entidad-relación;
- evidencia de conexión y carga.

### Fase 2

- validación de Bicep;
- despliegue con Azure CLI;
- recursos creados;
- contenedores Bronze, Silver y Gold;
- Key Vault;
- Log Analytics Workspace;
- Action Group.

### Fase 3

- ejecución de Bronze;
- columnas de auditoría;
- particionamiento;
- ejecución de Silver;
- registros rechazados;
- reporte de calidad;
- ejecución de Gold;
- conteos de dimensiones y hechos;
- archivos publicados en los contenedores.

### Fase 4

- ejecución local del orquestador;
- orden Bronze, Silver y Gold;
- número de intento;
- tiempo por capa;
- duración total;
- resultado final.

La ejecución completa puede guardarse con:

```powershell
python -m orchestration.run_pipeline 2>&1 |
    Tee-Object -FilePath docs\evidence\04_pipeline_ejecucion_completa.txt
```

---

## 18. Carga incremental

Bronze utiliza Azure SQL Change Tracking para identificar registros nuevos o modificados.

El comportamiento esperado es:

1. Se habilita Change Tracking.
2. La primera ejecución realiza la carga inicial.
3. Se guarda la última versión procesada.
4. Las siguientes ejecuciones consultan cambios posteriores.
5. Cuando no existen cambios, se procesan cero registros.

Ejemplo:

```text
MSTR_PROVEEDORES: 0 registros
MSTR_ARTICULOS: 0 registros
MSTR_TIENDAS: 0 registros
CRM_MIEMBROS: 0 registros
TRANS_VENTAS: 0 registros
INV_STOCK_DIARIO: 0 registros
POST_DEVOLUCIONES: 0 registros
Capa Bronze finalizada.
```

Este resultado indica que no se detectaron registros nuevos o modificados.

---

## 19. Alcance y limitaciones

El proyecto fue desarrollado como una prueba técnica end-to-end.

### Alcance implementado

- generación de datos sintéticos;
- configuración mediante YAML;
- semilla fija;
- exportación en CSV y Parquet;
- anomalías controladas;
- carga hacia Azure SQL Database;
- arquitectura Medallion;
- almacenamiento en ADLS Gen2;
- auditoría en Bronze;
- particionamiento por fecha;
- carga incremental;
- limpieza y estandarización en Silver;
- validación de integridad referencial;
- separación de errores;
- reporte de calidad;
- protección de identificadores sensibles;
- dimensiones y tablas de hechos;
- segmentación RFM;
- infraestructura mediante Bicep;
- parámetros para desarrollo y producción;
- despliegue mediante Azure CLI;
- orquestación local con Python;
- reintentos básicos;
- medición de tiempos;
- documentación y evidencias;
- versionamiento en GitHub.

### Limitaciones actuales

- los volúmenes se redujeron para trabajar con los recursos disponibles;
- la Fase 4 se ejecuta localmente;
- el orquestador requiere que el equipo local permanezca activo;
- la programación automática de ejecuciones no forma parte de la versión actual;
- Key Vault fue desplegado, pero la aplicación todavía utiliza variables de entorno;
- el monitoreo y las alertas se encuentran en una etapa base;
- las evidencias se conservan principalmente como capturas y archivos locales.

---

## 20. Próximos pasos

La principal mejora futura es migrar la Fase 4 hacia **Azure Data Factory**.

Esto permitiría:

- ejecutar el pipeline desde Azure;
- programar ejecuciones;
- configurar actividades por capa;
- establecer dependencias;
- administrar reintentos;
- consultar el historial de ejecuciones;
- centralizar el monitoreo;
- integrar alertas.

Otras mejoras posibles:

- integrar Key Vault directamente con el código;
- enviar logs hacia Log Analytics;
- configurar alertas mediante Action Group;
- ampliar las pruebas de calidad;
- incrementar gradualmente los volúmenes;
- conectar la capa Gold con una herramienta de visualización.

---

## Resultado final

El proyecto implementa el siguiente recorrido:

```text
Datos sintéticos
    -> Azure SQL Database
    -> Bronze en ADLS Gen2
    -> Silver en ADLS Gen2
    -> Gold en ADLS Gen2
```

La Fase 4 controla este flujo actualmente mediante un orquestador local en Python:

```text
Bronze -> Silver -> Gold
```

La solución demuestra generación de datos, fuente relacional, almacenamiento en la nube, procesamiento Medallion, calidad de datos, carga incremental, modelo analítico, infraestructura como código y orquestación local.