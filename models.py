from flask_sqlalchemy import SQLAlchemy
from numpy import True_
from datetime import datetime

# crear objeto base de datos
db = SQLAlchemy()  # crea el administrador de base de datos


class Tienda(db.Model):  # define una tabla
    # nombre tabla
    __tablename__ = "tiendas"  # nombre fisico de la tabla

    # id unico
    id = db.Column(
        db.Integer, primary_key=True
    )  # crea la columna ID, lo convierte en clave principal

    # sigla de tienda
    codigo = db.Column(
        db.String(10), unique=True, nullable=False
    )  # guarda las siglas de las tiendas unique=True impide repetir tiendas

    # nombre de tienda
    nombre = db.Column(db.String(100), nullable=False)

    # santiago o region
    zona = db.Column(db.String(10), nullable=False)

    # activo
    activo = db.Column(db.Boolean, default=True)


class Proveedor(db.Model):
    __tablename__ = "proveedores"

    id = db.Column(db.Integer, primary_key=True)

    nombre = db.Column(db.String(150), unique=True, nullable=False)

    activo = db.Column(db.Boolean, default=True)


class TipoCarga(db.Model):
    __tablename__ = "tipos_carga"

    id = db.Column(db.Integer, primary_key=True)

    nombre = db.Column(db.String(50), unique=True, nullable=False)


class Carga(db.Model):
    __tablename__ = "cargas"

    # identificador unico
    id = db.Column(db.Integer, primary_key=True)

    # fecha de carga
    fecha_carga = db.Column(db.DateTime, nullable=False)

    # nombre del archivo
    archivo = db.Column(db.String(255), nullable=False)

    # cantidad de registros cargados
    registros = db.Column(db.Integer, nullable=False)


class Consolidado(db.Model):
    __tablename__ = "consolidado"

    # ID
    id = db.Column(db.Integer, primary_key=True)

    # Orden de Compra OC
    oc = db.Column(db.String(50))

    # Factura
    factura = db.Column(db.String(50))

    # Tienda de destino
    destino = db.Column(db.String(20), nullable=False)

    # Nombre de Proveedor
    proveedor = db.Column(db.String(150))

    # Cantidad de Bultos
    bultos = db.Column(db.Integer, nullable=False)

    # Cantidad de unidades
    unidades = db.Column(db.String(50), nullable=False)

    # Tipo de carga = nacional,tester,mkt,etc
    tipo_carga = db.Column(db.String(50), nullable=False, default="NACIONAL")

    # etiqueta
    etiqueta = db.Column(db.String(150))

    # observacion: comentarios posteriores
    observacion = db.Column(db.String(500))

    # estado
    estado = db.Column(db.String(20), nullable=False, default="PENDIENTE")

    # origen NACIONAL o EXTERNO
    origen_archivo = db.Column(db.String(50), nullable=False)

    # nombre de archivo
    nombre_archivo = db.Column(db.String(255))

    # Fecha de carga al sistema
    fecha_carga = db.Column(db.DateTime)

    # historial de eliminados
    eliminado = db.Column(db.Boolean, nullable=False, default=False)

    # fecha de eliminación
    fecha_eliminacion = db.Column(db.DateTime)


class HistorialCarga(db.Model):
    __tablename__ = "historial_cargas"

    id = db.Column(db.Integer, primary_key=True)
    nombre_archivo = db.Column(db.String(255), nullable=False)
    registro_guardados = db.Column(db.Integer, nullable=False)
    duplicados = db.Column(db.Integer, nullable=False)
    conflictos = db.Column(db.Integer, nullable=False)
    errores = db.Column(db.Integer, nullable=False)
    fecha_carga = db.Column(db.DateTime, nullable=False)
