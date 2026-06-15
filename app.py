from calendar import c

from flask import Flask, render_template, request
from sqlalchemy import distinct
from config import Config
from models import Consolidado, HistorialCarga, Proveedor, db, Cuadratura
from datetime import datetime

import pandas as pd
import os  # Permite trabajar con archivos y carpetas

# crea aplicacion
app = Flask(__name__)

# cargar configuracion
app.config.from_object(Config)

# conectar SQLAlchemy
db.init_app(app)

# crea todas las tablas de models.py
with app.app_context():
    db.create_all()


# Ruta principal
@app.route("/")
def inicio():

    return """Sistema Packing List"""


@app.route("/dashboard")
def dashboard():

    return """Dashboard Packing List"""


@app.route("/registros")
def registros():
    oc = request.args.get("oc", "")
    factura = request.args.get("factura", "")
    destino = request.args.get("destino", "")
    proveedor = request.args.get("proveedor", "")
    estado = request.args.get("estado", "")

    consulta = Consolidado.query.filter_by(eliminado=False)
    if oc:
        consulta = consulta.filter(Consolidado.oc.contains(oc))
    if factura:
        consulta = consulta.filter(Consolidado.factura.contains(factura))
    if destino:
        consulta = consulta.filter(Consolidado.destino.contains(destino))
    if proveedor:
        consulta = consulta.filter(Consolidado.proveedor.contains(proveedor))
    if estado:
        consulta = consulta.filter(Consolidado.estado.contains(estado))

    registros = consulta.order_by(Consolidado.id.desc()).all()
    return render_template(
        "registros.html",
        registros=registros,
        oc=oc,
        factura=factura,
        destino=destino,
        proveedor=proveedor,
        estado=estado,
    )


@app.route("/despachos", methods=["GET", "POST"])
def despachos():
    if request.method == "POST":
        tiendas = request.form.getlist("tiendas")
        fecha_despacho = request.form["fecha_despacho"]
        registros = Consolidado.query.filter(
            Consolidado.destino.in_(tiendas),
            Consolidado.estado == "PENDIENTE",
            Consolidado.eliminado == False,
        ).all()

        cantidad = 0
        for registro in registros:
            registro.estado = "DESPACHADO"
            registro.fecha_despacho = datetime.strptime(fecha_despacho, "%Y-%m-%d")

            cantidad += 1

        db.session.commit()
        return f"""
        <h2>Despacho Realizado</h2>
        <p>
        <b>Tiendas seleccionadas: </b> {len(tiendas)}</p>
        <p>
        <b>Registros actualizados </b> {cantidad}</p>

        <a href="/despachos">Volver</a>
        """
    tiendas = (
        db.session.query(Consolidado.destino)
        .filter(Consolidado.estado == "PENDIENTE", Consolidado.eliminado == False)
        .distinct()
        .all()
    )
    return render_template("despachos.html", tiendas=tiendas)


@app.route("/revertir_despachos", methods=["GET", "POST"])
def revertir_despachos():
    tiendas = []
    fecha_buscada = ""

    if request.method == "POST":
        accion = request.form.get("accion")
        fecha_buscada = request.form["fecha_despacho"]
        fecha = datetime.strptime(fecha_buscada, "%Y-%m-%d").date()

        # BUSCAR TIENDAS

        if accion == "buscar":

            registros = Consolidado.query.filter(
                Consolidado.estado == "DESPACHADO"
            ).all()

            destinos = set()

            for registro in registros:
                if registro.fecha_despacho and registro.fecha_despacho.date() == fecha:
                    destinos.add(registro.destino)
            tiendas = sorted(list(destinos))

        # REVERTIR
        elif accion == "revertir":
            tiendas_seleccionadas = request.form.getlist("tiendas")

            registros = Consolidado.query.filter(
                Consolidado.estado == "DESPACHADO",
                Consolidado.destino.in_(tiendas_seleccionadas),
            ).all()

            cantidad = 0

            for registro in registros:
                if registro.fecha_despacho and registro.fecha_despacho.date() == fecha:
                    registro.estado = "PENDIENTE"
                    registro.fecha_despacho = None

                    cantidad += 1
            db.session.commit()

            return f"""
            <h2>Reversa Completada</h2>
            <p>Registro afectados: {cantidad}</p>
            <a href="/revertir_despachos"></a>
            """
    return render_template(
        "revertir_despachos.html", tiendas=tiendas, fecha_buscada=fecha_buscada
    )


@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    registro = Consolidado.query.get_or_404(id)
    if request.method == "POST":
        registro.factura = request.form["factura"]
        registro.destino = request.form["destino"]
        registro.proveedor = request.form["proveedor"]
        registro.estado = request.form["estado"]
        fecha_despacho = request.form.get("fecha_despacho")

        if registro.estado == "DESPACHADO":
            if not fecha_despacho:
                return """
                Error: Debe indicar una fecha de despacho.
                <br><br>

                <a href ="javascript:history.black()">
                Volver
                </a>
                """
            registro.fecha_despacho = datetime.strptime(fecha_despacho, "%Y-%m-%d")
        else:
            registro.fecha_despacho = None

        db.session.commit()

        return """Registro actualizado correctamente
            <br><br>
            <a href="/registros">Volver</a>
        """
    return render_template("editar.html", registro=registro)


@app.route("/eliminar/<int:id>")
def eliminar(id):
    registro = Consolidado.query.get_or_404(id)
    registro.eliminado = True
    registro.fecha_eliminacion = datetime.now()
    db.session.commit()
    return """Registro eliminado correctamente
        <br><br>
        <a href="/registros">Volver al listado</a>
    """


@app.route("/actualizar_estado", methods=["POST"])
def actualizar_estado():
    ids = request.form.getlist("ids")
    nuevo_estado = request.form["nuevo_estado"]
    fecha_despacho = request.form.get("fecha_despacho")

    actualizados = 0

    if nuevo_estado == "DESPACHADO":
        if not fecha_despacho:
            return """
            Debe indicar una fecha de despacho
            <br><br>
            <a href="/registros">Volver</a>
            """
        fecha = datetime.strptime(fecha_despacho, "%Y-%m-%d")

    for id_registro in ids:
        registro = Consolidado.query.get(int(id_registro))

        if not registro:
            continue
        if nuevo_estado == "DESPACHADO":
            registro.estado = "PENDIENTE"
            registro.fecha_despacho = fecha
        else:
            registro.estado = "PENDIENTE"
            registro.fecha_despacho = None

        actualizados += 1
    db.session.commit()
    return f"""
        <h2>Actualizacion completada</h2>
        Registros actualizados: {actualizados}
        <br><br>
        <a href="/registros">Volver al listado</a>
    """


@app.route("/cuadraturas")
def cuadraturas():

    cuadraturas = Cuadratura.query.order_by(Cuadratura.id.desc()).all()

    return render_template("cuadraturas.html", cuadraturas=cuadraturas)


@app.route("/crear_cuadratura", methods=["GET", "POST"])
def crear_cuadratura():
    if request.method == "POST":
        nueva = Cuadratura(
            nombre_archivo=request.form["nombre_archivo"],
            responsable=request.form["responsable"],
            observacion=request.form["observacion"],
        )
        db.session.add(nueva)
        db.session.commit()

        return """
        Cuadratura creada
        <br><br>
        <a href="/cuadraturas">Volver</a>
        """
    archivos = (
        db.session.query(Consolidado.nombre_archivo)
        .distinct()
        .order_by(Consolidado.nombre_archivo.desc())
        .all()
    )

    return render_template("crear_cuadratura.html", archivos=archivos)


@app.route("/importar", methods=["GET", "POST"])
def importar():

    if request.method == "POST":

        # Obtener archivo enviado desde el formulario
        archivo = request.files["archivo"]

        # Construir ruta donde se guardará
        ruta_archivo = os.path.join("uploads", archivo.filename)

        # Guardar archivo físicamente
        archivo.save(ruta_archivo)

        # Abrir Excel
        excel = pd.ExcelFile(ruta_archivo)

        # Obtener nombres de hojas
        hojas = excel.sheet_names

        # Convertir a mayúsculas para evitar problemas
        hojas_mayusculas = [hoja.upper() for hoja in hojas]

        # Validar existencia de hoja CONSOLIDADO
        if "CONSOLIDADO" not in hojas_mayusculas:

            return "ERROR: No existe la hoja CONSOLIDADO"

        # Leer hoja CONSOLIDADO
        df = pd.read_excel(ruta_archivo, sheet_name="CONSOLIDADO", header=1)

        # Buscar fila RESPONSABLE NACIONAL
        buscar_fin = df[
            df["Nro. OC"]
            .astype(str)
            .str.contains("RESPONSABLE NACIONAL", case=False, na=False)
        ]

        if not buscar_fin.empty:

            fila_fin = buscar_fin.index[0]

            df = df.iloc[:fila_fin]

        # Eliminar filas sin OC
        df = df.dropna(subset=["Nro. OC"], how="all")

        columnas_esperadas = [
            "Nro. OC",
            "Nro.Docto.",
            "Destino",
            "PROVEEDOR",
            "Bultos",
            "Unidades",
        ]
        for columna in columnas_esperadas:
            if columna not in df.columns:
                return f"ERROR: Falta la columna: {columna}"

        df = df.rename(
            columns={
                "Nro. OC": "OC",
                "Nro.Docto.": "FACTURA",
                "Destino": "DESTINO",
                "PROVEEDOR": "PROVEEDOR",
                "Bultos": "BULTOS",
                "Unidades": "UNIDADES",
            }
        )

        # limpieza de espacios multiples
        for columna in ["OC", "FACTURA", "DESTINO", "PROVEEDOR", "UNIDADES"]:
            df[columna] = df[columna].fillna("").astype(str).str.strip()

            df["PROVEEDOR"] = df["PROVEEDOR"].str.split().str.join(" ")

            df["OC"] = df["OC"].replace(
                ["", "nan", "None"], "S/OC"
            )  # reemplaza las OC vacias por S/OC
            df["FACTURA"] = df["FACTURA"].replace(
                ["", "nan", "None"], "S-G"
            )  # reemplaza las FACTURAS vacias por S-G
            df["UNIDADES"] = df["UNIDADES"].replace(
                ["", "nan", "None"], "S/INFO"
            )  # reemplaza las UNIDADES vacias por S/INFO
            df["BULTOS"] = (
                pd.to_numeric(df["BULTOS"], errors="coerce").fillna(0).astype(int)
            )
            df["UNIDADES"] = (
                df["UNIDADES"].astype(str).str.replace(".0", "", regex=False)
            )
        guardados = 0
        duplicados = 0
        conflictos = 0
        errores = 0
        lista_duplicados = []
        lista_conflictos = []
        lista_errores = []

        errores_excel = []

        for _, fila in df.iterrows():
            try:

                existe = Consolidado.query.filter_by(
                    oc=fila["OC"],
                    factura=fila["FACTURA"],
                    destino=fila["DESTINO"],
                    proveedor=fila["PROVEEDOR"],
                ).first()

                if existe:
                    duplicados += 1
                    lista_duplicados.append(f"""
                        OC: {fila["OC"]} |
                        FACTURA: {fila["FACTURA"]} |
                        DESTINO: {fila["DESTINO"]}
                        """)

                    errores_excel.append(
                        {
                            "Tipo Error": " DUPLICADO",
                            "OC": fila["OC"],
                            "FACTURA": fila["FACTURA"],
                            "DESTINO": fila["DESTINO"],
                            "PROVEEDOR": fila["PROVEEDOR"],
                            "MOTIVO": "Registro ya existe en la base de datos",
                        }
                    )
                    continue

                if fila["OC"] != "S/OC":

                    registro_oc = Consolidado.query.filter_by(oc=fila["OC"]).first()

                    if registro_oc and registro_oc.proveedor != fila["PROVEEDOR"]:

                        conflictos += 1

                        lista_conflictos.append(f"""
                          OC: {fila["OC"]} |
                            PROVEEDOR EXISTENTE: {registro_oc.proveedor} |
                            PROVEEDOR RECIBIDO: {fila["PROVEEDOR"]}
                            """)
                        errores_excel.append(
                            {
                                "Tipo Error": "CONFLICTO",
                                "OC": fila["OC"],
                                "FACTURA": fila["FACTURA"],
                                "DESTINO": fila["DESTINO"],
                                "PROVEEDOR": fila["PROVEEDOR"],
                                "MOTIVO": f"La OC pertenece a {registro_oc.proveedor}",
                            }
                        )
                        print("conflicto agregado a excel")
                        continue

                nuevo = Consolidado(
                    oc=fila["OC"],
                    factura=fila["FACTURA"],
                    destino=fila["DESTINO"],
                    proveedor=fila["PROVEEDOR"],
                    bultos=fila["BULTOS"],
                    unidades=fila["UNIDADES"],
                    tipo_carga="NACIONAL",
                    origen_archivo="NACIONAL",
                    nombre_archivo=archivo.filename,
                    fecha_carga=datetime.now(),
                )
                db.session.add(nuevo)
                guardados += 1
            except Exception as e:
                errores += 1
                lista_errores.append(f"""
                                 OC: {fila["OC"],""} |
                                 FACTURA: {fila["FACTURA"],""} |
                                 ERROR: {str(e)}
                                 """)
            continue

        db.session.commit()
        historial = HistorialCarga(
            nombre_archivo=archivo.filename,
            registro_guardados=guardados,
            duplicados=duplicados,
            conflictos=conflictos,
            errores=errores,
            fecha_carga=datetime.now(),
        )
        db.session.add(historial)
        db.session.commit()

        if errores_excel:

            df_errores = pd.DataFrame(errores_excel)

            ruta_errores = os.path.join("uploads", "errores_importacion.xlsx")

            df_errores.to_excel(ruta_errores, index=False)

        duplicados_html = "<br>".join(lista_duplicados)
        conflictos_html = "<br>".join(lista_conflictos)
        errores_html = "<br>".join(lista_errores)

        return f"""
        <h2>Carga Finalizada</h2>
        <p><b>Registros guardados: </b> {guardados} </p>
        <p><b>Duplicados detectados: </b> {duplicados} </p>
        <p><b>Conflictos proveedor: </b> {conflictos} </p>
        <p><b>Errores: </b> {errores} </p>
        <hr>
        <h3>Detalle duplicados</h3>
        {duplicados_html}
        <hr>
        <h3>Detalle Conflictos OC - Proveedor</h3>
        {conflictos_html}
        <hr>
        <h3>Detalle Errores</h3>
        {errores_html}
        <hr>
        <p><b>Archivo de errores generado: </b> uploads/errores_importacion.xlsx </p>
        """
    return render_template("importar_excel.html")


# ejecutar servidor
if __name__ == "__main__":
    app.run(debug=True)  # levanta el servidor local
