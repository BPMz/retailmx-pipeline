# Infraestructura Azure - RetailMax

## Descripción

Esta carpeta contiene la infraestructura como código (IaC) desarrollada para la prueba técnica de RetailMax.

La implementación fue realizada utilizando **Bicep** como lenguaje de definición de infraestructura y **Azure CLI** como herramienta de despliegue.

El objetivo de esta fase es crear la infraestructura base necesaria para soportar el pipeline de datos y la arquitectura Medallion.

> Esta implementación representa una base funcional y no una plataforma productiva completa.

---

# Arquitectura implementada

La infraestructura creada es:

```
Azure Subscription

└── Resource Group

    ├── Azure Data Lake Storage Gen2
    │
    │   ├── bronze
    │   ├── silver
    │   └── gold
    │
    ├── Azure Data Factory
    │
    ├── Azure Key Vault
    │
    ├── Log Analytics Workspace
    │
    └── Action Group
```

---

# Recursos implementados

## Azure Data Lake Storage Gen2

Se creó un Storage Account habilitado para Azure Data Lake Storage Gen2 mediante:

```
isHnsEnabled = true
```

Esto permite utilizar una estructura jerárquica de almacenamiento necesaria para implementar el modelo Medallion.

Las capas creadas son:

- **Bronze:** almacenamiento de datos originales sin transformaciones.
- **Silver:** almacenamiento de datos procesados y estandarizados.
- **Gold:** almacenamiento de información preparada para consumo analítico.

---

## Azure Data Factory

Se creó Azure Data Factory como servicio de orquestación para los procesos de datos.

Su objetivo será permitir posteriormente:

- extracción de información desde fuentes de datos,
- movimiento de datos,
- ejecución de procesos ETL/ELT.

En esta fase solamente se realizó el aprovisionamiento del recurso.

---

## Azure Key Vault

Se creó Azure Key Vault como componente para la gestión segura de secretos y credenciales.

Durante esta fase no se almacenaron secretos ni credenciales.

---

## Log Analytics Workspace

Se creó un Workspace de Log Analytics como base para monitoreo y almacenamiento de registros de Azure.

---

## Action Group

Se creó un Action Group como componente base para la gestión de notificaciones y alertas.

La configuración de reglas específicas de alertas queda pendiente para fases posteriores.

---

# Lista de recursos creados

| Recurso | Región | Propósito dentro de la solución |
|---|---|---|
| Resource Group | East US | Contenedor lógico donde se agrupan todos los recursos de la solución |
| Azure Data Lake Storage Gen2 | East US | Almacenamiento principal para las capas Bronze, Silver y Gold |
| Contenedor Bronze | East US | Almacenamiento de datos originales sin transformación |
| Contenedor Silver | East US | Almacenamiento de datos procesados y estandarizados |
| Contenedor Gold | East US | Almacenamiento de datos preparados para consumo analítico |
| Azure Data Factory | East US | Orquestación de procesos de extracción y transformación |
| Azure Key Vault | East US | Gestión segura de secretos y credenciales futuras |
| Log Analytics Workspace | East US | Base para monitoreo y almacenamiento de registros |
| Action Group | Global | Gestión de notificaciones y alertas |

---

# Estructura de archivos

```
infra/

├── main.bicep
│
│   Archivo principal del despliegue.
│   Crea el Resource Group y ejecuta el módulo de recursos.
│
├── resources.bicep
│
│   Contiene la definición de los recursos Azure.
│
├── main.dev.bicepparam
│
│   Parámetros utilizados para el ambiente de desarrollo.
│
├── main.prod.bicepparam
│
│   Parámetros preparados para el ambiente productivo.
│
└── README.md
```

---

# Parámetros por ambiente

La infraestructura utiliza archivos `.bicepparam` para separar la configuración del ambiente del código principal.

Esto permite reutilizar la misma definición de infraestructura para diferentes ambientes sin duplicar código.

Archivos utilizados:

```
main.dev.bicepparam
main.prod.bicepparam
```

Los archivos contienen únicamente parámetros de configuración del ambiente.

No contienen credenciales, contraseñas o secretos.

---

# Requisitos

Para realizar el despliegue se requiere:

- Cuenta activa de Azure.
- Azure CLI instalado.
- Bicep habilitado mediante Azure CLI.

Verificación:

```powershell
az --version

az bicep version
```

Inicio de sesión:

```powershell
az login
```

---

# Validación de infraestructura

Antes del despliegue se realizó una validación de la plantilla Bicep:

```powershell
az deployment sub validate `
  --location eastus `
  --template-file .\infra\main.bicep `
  --parameters .\infra\main.dev.bicepparam
```

Esta validación permite comprobar:

- sintaxis del código Bicep,
- estructura de recursos,
- parámetros definidos,
- compatibilidad del despliegue.

Este comando no crea recursos en Azure.

---

# Simulación del despliegue

Se utilizó `what-if` para revisar los cambios antes de aplicar la infraestructura:

```powershell
az deployment sub what-if `
  --location eastus `
  --template-file .\infra\main.bicep `
  --parameters .\infra\main.dev.bicepparam
```

Esto permite identificar los recursos que serán creados antes del despliegue real.

---

# Despliegue con Azure CLI

El despliegue de infraestructura se realizó mediante Azure CLI:

```powershell
az deployment sub create `
  --location eastus `
  --template-file .\infra\main.bicep `
  --parameters .\infra\main.dev.bicepparam
```

Resultado esperado:

```
provisioningState: Succeeded
```

Esto confirma que Azure creó correctamente los recursos definidos en la plantilla.

---

# Verificación del despliegue

Consultar estado del despliegue:

```powershell
az deployment sub show `
  --name main `
  --query properties.provisioningState
```

Consultar recursos creados:

```powershell
az resource list `
  --resource-group <resource-group-name> `
  --output table
```

---

# Justificación técnica

## ¿Por qué Bicep?

Se utilizó Bicep porque es una herramienta nativa de Azure para definir infraestructura como código.

Sus principales ventajas son:

- Permite crear infraestructura de forma reproducible.
- Evita configuraciones manuales desde el portal.
- Facilita mantener la infraestructura versionada.
- Permite separar código y configuración mediante parámetros.
- Tiene integración directa con Azure Resource Manager.

Para esta prueba técnica, Bicep permite implementar una solución simple, clara y alineada con los servicios Azure utilizados.

---

## ¿Por qué Azure CLI?

Se utilizó Azure CLI porque permite administrar y desplegar recursos Azure desde línea de comandos.

Sus ventajas son:

- Permite validar y desplegar archivos Bicep.
- Facilita repetir despliegues.
- Puede integrarse posteriormente en procesos CI/CD.
- Es una herramienta oficial de Microsoft Azure.

---

## ¿Por qué Azure Data Lake Storage Gen2?

Se utilizó ADLS Gen2 porque está diseñado para almacenar grandes volúmenes de datos analíticos.

Además permite implementar la arquitectura Medallion:

```
Bronze → Silver → Gold
```

Separando datos originales, transformados y preparados para consumo analítico.

---

## ¿Por qué Azure Data Factory?

Se utilizó Data Factory porque es el servicio de Azure orientado a la orquestación de procesos de datos.

Permitirá posteriormente coordinar extracción, transformación y carga de información.

---

## ¿Por qué Key Vault?

Se incorporó Key Vault como componente de seguridad para gestionar secretos de forma centralizada.

Esto evita almacenar información sensible directamente en código fuente.

---

# Limitaciones y pendientes de esta fase

La implementación cumple con la creación de la infraestructura base solicitada.

Los siguientes puntos quedan pendientes para fases posteriores:

## Integración del pipeline

Pendiente:

- conexiones con fuentes de datos,
- linked services,
- datasets,
- pipelines,
- triggers.

---

## Seguridad avanzada

No se implementaron:

- redes privadas,
- private endpoints,
- reglas avanzadas de firewall,
- permisos RBAC específicos entre servicios.

---

## Monitoreo avanzado

No se configuraron:

- reglas específicas de alertas,
- diagnósticos avanzados,
- métricas personalizadas.

---

## Gestión de secretos

No se agregaron secretos en Key Vault durante esta fase.

La configuración de credenciales se realizará cuando sea necesaria para las conexiones del pipeline.

---

# Estado final

La infraestructura fue desplegada correctamente mediante Bicep y Azure CLI.

Esta implementación deja preparada la base necesaria para continuar con la construcción del pipeline de datos y el modelo Medallion en las siguientes fases.