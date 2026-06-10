# Contexto de la aplicación

## Propósito
Esta aplicación es un sistema Flask para procesar y cargar archivos Excel de tipo "Packing List" nacional en una base de datos SQLite.

## Componentes principales

- `app.py`
  - Inicializa la app Flask.
  - Carga configuración desde `config.py`.
  - Inicializa SQLAlchemy y crea las tablas al arrancar.
  - Expone rutas:
    - `/` : mensaje de bienvenida.
    - `/dashboard` : mensaje de dashboard.
    - `/importar` : formulario para subir el archivo Excel y proceso de importación.

- `config.py`
  - Define la configuración de la base de datos.
  - Usa `SQLALCHEMY_DATABASE_URI = "sqlite:///sistema.db"`.
  - Desactiva los mensajes de seguimiento con `SQLALCHEMY_TRACK_MODIFICATIONS = false`.

- `models.py`
  - Define los modelos SQLAlchemy:
    - `Tienda` (tabla `tiendas`)
    - `Proveedor` (tabla `proveedores`)
    - `TipoCarga` (tabla `tipos_carga`)
    - `Carga` (tabla `cargas`)
    - `Consolidado` (tabla `consolidado`)
  - La aplicación actual utiliza principalmente el modelo `Consolidado` para almacenar registros de importación.

- `templates/`
  - `importar_excel.html` : formulario usado por la ruta `/importar`.
  - `base.html` y `dashboard.html` : plantillas presentes en la aplicación.

- `uploads/`
  - Carpeta donde se guarda el archivo Excel subido antes de procesarlo.

## Flujo de importación de Excel

1. El usuario envía un archivo Excel desde `/importar`.
2. El archivo se guarda en `uploads/`.
3. Se abre con `pandas.ExcelFile` y se buscan las hojas.
4. El sistema valida que exista la hoja `CONSOLIDADO`.
5. Se lee la hoja `CONSOLIDADO` con `header=1`.
6. Si aparece una fila con `RESPONSABLE NACIONAL`, el procesamiento se detiene antes de esa fila.
7. Se eliminan filas sin valor en `Nro. OC`.
8. Se validan las columnas esperadas:
   - `Nro. OC`
   - `Nro.Docto.`
   - `Destino`
   - `PROVEEDOR`
   - `Bultos`
   - `Unidades`
9. Se renombran las columnas a:
   - `OC`, `FACTURA`, `DESTINO`, `PROVEEDOR`, `BULTOS`, `UNIDADES`
10. Se limpian espacios y se reemplazan valores faltantes:
    - OC vacías → `S/OC`
    - FACTURA vacías → `S-G`
    - UNIDADES vacías → `S/INFO`
11. Se normaliza `BULTOS` a entero y se limpia `UNIDADES`.

## Reglas de negocio durante la carga

- Se buscan duplicados exactos de `OC`, `FACTURA`, `DESTINO` y `PROVEEDOR`.
- Si existe el mismo `OC` con distinto `PROVEEDOR`, se considera un conflicto y no se guarda ese registro.
- Los registros válidos se guardan en la tabla `consolidado` con campos adicionales:
  - `tipo_carga` = `NACIONAL`
  - `origen_archivo` = `NACIONAL`
  - `nombre_archivo` = nombre del archivo subido
  - `fecha_carga` = fecha y hora actual

## Base de datos

- Motor: SQLite.
- Archivo de base de datos: `sistema.db`.
- Tablas creadas automáticamente al iniciar la app.

## Observaciones

- Actualmente las rutas `/` y `/dashboard` devuelven solo texto.
- La ruta `/importar` devuelve un resumen HTML del resultado de la importación con conteos de registros guardados, duplicados y conflictos.
- La aplicación corre en modo debug cuando se ejecuta con `python app.py`.
