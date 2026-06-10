from flask import (
    Flask,
    render_template,
    request,
)  # request permite acceder a lo que envia el navegador
from config import Config
from models import Consolidado, Proveedor, db
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
                        EXISTENTE: {registro_oc.proveedor} |
                        RECIBIDO: {fila["PROVEEDOR"]}
                        """)
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
