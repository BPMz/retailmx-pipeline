/* Generación y carga de datos sintéticos

Crear en Azure SQL Database las siete tablas relacionales que actuarán como fuente de origen del pipeline de datos. */

SET NOCOUNT ON;
GO

/* CREACIÓN DEL ESQUEMA SOURCE*/
IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = N'source'
)
BEGIN
    EXEC(N'CREATE SCHEMA [source] AUTHORIZATION [dbo]');
END;
GO


/* ELIMINACIÓN DE TABLAS ANTERIORES */
DROP TABLE IF EXISTS [source].[POST_DEVOLUCIONES];
DROP TABLE IF EXISTS [source].[INV_STOCK_DIARIO];
DROP TABLE IF EXISTS [source].[TRANS_VENTAS];
DROP TABLE IF EXISTS [source].[CRM_MIEMBROS];
DROP TABLE IF EXISTS [source].[MSTR_ARTICULOS];
DROP TABLE IF EXISTS [source].[MSTR_TIENDAS];
DROP TABLE IF EXISTS [source].[MSTR_PROVEEDORES];
GO


/* TABLA DE PROVEEDORES
Es la primera tabla que se crea porque MSTR_ARTICULOS depende de ella. */
CREATE TABLE [source].[MSTR_PROVEEDORES] (
    [id_proveedor] INT NOT NULL,
    [razon_social] NVARCHAR(200) NOT NULL,
    [pais_origen] NVARCHAR(50) NOT NULL,
    [tiempo_repo_dias] SMALLINT NOT NULL,
    [calificacion_calidad] DECIMAL(4, 2) NOT NULL,
    [activo] BIT NOT NULL,

    CONSTRAINT [PK_MSTR_PROVEEDORES]
        PRIMARY KEY ([id_proveedor])
);
GO


/* TABLA DE ARTÍCULOS
id_proveedor relaciona cada artículo con un proveedor existente.*/
CREATE TABLE [source].[MSTR_ARTICULOS] (
    [art_id] INT NOT NULL,
    [cod_barra] VARCHAR(13) NOT NULL,
    [desc_art] NVARCHAR(250) NOT NULL,
    [id_categ_n1] NVARCHAR(100) NOT NULL,
    [id_categ_n2] NVARCHAR(120) NOT NULL,
    [id_categ_n3] NVARCHAR(150) NOT NULL,
    [id_proveedor] INT NOT NULL,
    [precio_lista] DECIMAL(18, 2) NOT NULL,
    [peso_kg] DECIMAL(12, 3) NULL,
    [unid_medida] NVARCHAR(30) NOT NULL,
    [activo] BIT NOT NULL,
    [fec_alta] DATE NOT NULL,

    CONSTRAINT [PK_MSTR_ARTICULOS]
        PRIMARY KEY ([art_id]),
        
    CONSTRAINT [FK_ARTICULOS_PROVEEDORES]
        FOREIGN KEY ([id_proveedor])
        REFERENCES [source].[MSTR_PROVEEDORES] ([id_proveedor])
);
GO


/* TABLA DE TIENDAS
Contiene las tiendas físicas y digitales de RetailMax.*/
CREATE TABLE [source].[MSTR_TIENDAS] (
    [id_tienda] INT NOT NULL,
    [nom_tienda] NVARCHAR(200) NOT NULL,
    [tipo_tienda] NVARCHAR(50) NOT NULL,
    [id_ciudad] VARCHAR(20) NOT NULL,
    [id_pais] NVARCHAR(50) NOT NULL,
    [metros_cuadrados] INT NULL,
    [activo] BIT NOT NULL,
    [fec_apertura] DATE NOT NULL,

    CONSTRAINT [PK_MSTR_TIENDAS]
        PRIMARY KEY ([id_tienda])
);
GO


/* TABLA DE MIEMBROS
Contiene los clientes registrados en el programa de fidelización. */
CREATE TABLE [source].[CRM_MIEMBROS] (
    [id_miembro] INT NOT NULL,
    [fec_registro] DATE NOT NULL,
    [id_ciudad] VARCHAR(20) NOT NULL,
    [genero] NVARCHAR(30) NULL,
    [rango_edad] NVARCHAR(20) NULL,
    [canal_pref] NVARCHAR(50) NULL,
    [activo] BIT NOT NULL,
    [fec_ultima_compra] DATE NULL,

    CONSTRAINT [PK_CRM_MIEMBROS]
        PRIMARY KEY ([id_miembro])
);
GO


/* TABLA DE VENTAS
Contiene las transacciones realizadas por los clientes.
   Las ventas se relacionan con: CRM_MIEMBROS, MSTR_TIENDAS, MSTR_ARTICULOS */
CREATE TABLE [source].[TRANS_VENTAS] (
    [id_trans] BIGINT NOT NULL,
    [id_miembro] INT NULL,
    [id_tienda] INT NOT NULL,
    [art_id] INT NOT NULL,
    [fec_trans] DATE NOT NULL,
    [hra_trans] TIME(0) NOT NULL,
    [qty_vendida] SMALLINT NOT NULL,
    [precio_unitario_venta] DECIMAL(18, 2) NOT NULL,
    [descuento_aplicado] DECIMAL(18, 2) NOT NULL,
    [tipo_pago] NVARCHAR(50) NOT NULL,
    [canal_venta] NVARCHAR(50) NOT NULL,

    CONSTRAINT [PK_TRANS_VENTAS]
        PRIMARY KEY ([id_trans]),

    CONSTRAINT [FK_VENTAS_MIEMBROS]
        FOREIGN KEY ([id_miembro])
        REFERENCES [source].[CRM_MIEMBROS] ([id_miembro]),

    CONSTRAINT [FK_VENTAS_TIENDAS]
        FOREIGN KEY ([id_tienda])
        REFERENCES [source].[MSTR_TIENDAS] ([id_tienda]),

    CONSTRAINT [FK_VENTAS_ARTICULOS]
        FOREIGN KEY ([art_id])
        REFERENCES [source].[MSTR_ARTICULOS] ([art_id])
);
GO


/* TABLA DE INVENTARIO
Se relaciona con artículos y tiendas para posteriormente calcular riesgo de
quiebre, disponibilidad y necesidades de reposición.*/
CREATE TABLE [source].[INV_STOCK_DIARIO] (
    [id_snapshot] BIGINT NOT NULL,
    [art_id] INT NOT NULL,
    [id_tienda] INT NOT NULL,
    [fec_snapshot] DATE NOT NULL,
    [stock_fisico] INT NOT NULL,
    [stock_transito] INT NOT NULL,
    [stock_reservado] INT NOT NULL,
    [stock_minimo_config] INT NOT NULL,
    [stock_maximo_config] INT NOT NULL,

    CONSTRAINT [PK_INV_STOCK_DIARIO]
        PRIMARY KEY ([id_snapshot]),

    CONSTRAINT [FK_STOCK_ARTICULOS]
        FOREIGN KEY ([art_id])
        REFERENCES [source].[MSTR_ARTICULOS] ([art_id]),

    CONSTRAINT [FK_STOCK_TIENDAS]
        FOREIGN KEY ([id_tienda])
        REFERENCES [source].[MSTR_TIENDAS] ([id_tienda])
);
GO


/* TABLA DE DEVOLUCIONES
Contiene las devoluciones asociadas con una venta original.
La devolución se relaciona con: La venta original. El artículo devuelto. La tienda que procesa la devolución. */
CREATE TABLE [source].[POST_DEVOLUCIONES] (
    [id_devolucion] BIGINT NOT NULL,
    [id_trans_origen] BIGINT NOT NULL,
    [art_id] INT NOT NULL,
    [id_tienda] INT NOT NULL,
    [fec_devolucion] DATE NOT NULL,
    [qty_devuelta] SMALLINT NOT NULL,
    [motivo_cod] NVARCHAR(50) NULL,
    [canal_devolucion] NVARCHAR(50) NOT NULL,
    [estado_devolucion] NVARCHAR(30) NOT NULL,
    [vr_reembolso] DECIMAL(18, 2) NOT NULL,

    CONSTRAINT [PK_POST_DEVOLUCIONES]
        PRIMARY KEY ([id_devolucion]),

    CONSTRAINT [FK_DEVOLUCIONES_VENTAS]
        FOREIGN KEY ([id_trans_origen])
        REFERENCES [source].[TRANS_VENTAS] ([id_trans]),

    CONSTRAINT [FK_DEVOLUCIONES_ARTICULOS]
        FOREIGN KEY ([art_id])
        REFERENCES [source].[MSTR_ARTICULOS] ([art_id]),

    CONSTRAINT [FK_DEVOLUCIONES_TIENDAS]
        FOREIGN KEY ([id_tienda])
        REFERENCES [source].[MSTR_TIENDAS] ([id_tienda])
);
GO


/* MENSAJE DE CONFIRMACIÓN */
PRINT 'Esquema source y siete tablas de RetailMax creados correctamente.';
GO