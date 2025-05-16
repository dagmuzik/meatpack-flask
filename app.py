from flask import Flask, render_template, request
from sneakerhunt import buscar_todos, ejecutar_scraping_general
import json
import glob
import os

app = Flask(__name__)

# 🔄 Cargar productos nuevos desde el archivo más reciente
def obtener_ultimos_nuevos(path="data"):
    archivos = sorted(glob.glob(f"{path}/nuevos_*.json"))
    if not archivos:
        return []
    with open(archivos[-1], encoding="utf-8") as f:
        return json.load(f)

@app.route("/", methods=["GET", "POST"])
def index():
    productos = None
    talla = ""
    tienda = ""
    marca = ""
    genero = ""

    if request.method == "POST":
        talla = request.form.get("talla", "").strip()
        tienda = request.form.get("tienda", "").strip()
        marca = request.form.get("marca", "").strip()
        genero = request.form.get("genero", "").strip()
        productos = buscar_todos(talla=talla, tienda=tienda, marca=marca, genero=genero)

    nuevos = obtener_ultimos_nuevos()

    return render_template("index.html",
                           productos=productos,
                           talla=talla,
                           tienda=tienda,
                           marca=marca,
                           genero=genero,
                           nuevos=nuevos)

# ✅ Ruta para ejecutar scraping desde cronjob.org
@app.route("/cron/ejecutar-scraper")
def ejecutar_scraper_remoto():
    try:
        ejecutar_scraping_general()
        return "✅ Scraper ejecutado correctamente desde cron"
    except Exception as e:
        return f"❌ Error al ejecutar scraper: {e}"

if __name__ == "__main__":
    app.run(debug=True)

@app.route("/ver-cache")
def ver_ultimo_cache():
    import glob
    import json
    import os

    archivos = sorted(glob.glob("data/cache_*.json"))
    if not archivos:
        return "❌ No hay archivos de cache disponibles."

    ultimo = archivos[-1]
    try:
        with open(ultimo, encoding="utf-8") as f:
            data = json.load(f)
            productos = data.get("productos") or []
            return {
                "archivo": os.path.basename(ultimo),
                "total": len(productos),
                "preview": productos[:5]
            }
    except Exception as e:
        return f"❌ Error leyendo el archivo: {e}"

@app.route("/ver-errores")
def ver_errores_sin_precio():
    import glob
    import json
    import os

    archivos = sorted(glob.glob("data/errores_sin_precio_*.json"))
    if not archivos:
        return "✅ No hay errores registrados."

    ultimo = archivos[-1]
    with open(ultimo, encoding="utf-8") as f:
        data = json.load(f)
        return {
            "archivo": os.path.basename(ultimo),
            "total_errores": len(data),
            "preview": data[:5]
        }

@app.route("/cron/scrap-raw")
def scrap_raw_remote():
    try:
        from sneakerhunt import scrap_raw_shopify
        scrap_raw_shopify()
        return "✅ Datos RAW de Shopify guardados correctamente"
    except Exception as e:
        return f"❌ Error al ejecutar scrap RAW: {e}"

@app.route("/ver-raw")
def ver_raw_shopify():
    import glob
    import json
    import os

    archivos_meatpack = sorted(glob.glob("data/raw_meatpack_*.json"))
    archivos_lagrieta = sorted(glob.glob("data/raw_lagrieta_*.json"))

    if not archivos_meatpack and not archivos_lagrieta:
        return "❌ No hay archivos RAW disponibles."

    ultimo_meat = archivos_meatpack[-1] if archivos_meatpack else None
    ultimo_grieta = archivos_lagrieta[-1] if archivos_lagrieta else None

    preview = {}

    if ultimo_meat:
        with open(ultimo_meat, encoding="utf-8") as f:
            data = json.load(f)
            preview["Meatpack"] = {
                "archivo": os.path.basename(ultimo_meat),
                "productos": data.get("products", [])[:3]
            }

    if ultimo_grieta:
        with open(ultimo_grieta, encoding="utf-8") as f:
            data = json.load(f)
            preview["La Grieta"] = {
                "archivo": os.path.basename(ultimo_grieta),
                "productos": data.get("products", [])[:3]
            }

    return preview

from flask import send_file, request

@app.route("/descargar-raw")
def descargar_raw():
    import glob
    import os

    tienda = request.args.get("tienda", "").lower()
    if tienda not in ["meatpack", "lagrieta"]:
        return "❌ Parámetro inválido. Usá ?tienda=meatpack o ?tienda=lagrieta"

    archivos = sorted(glob.glob(f"data/raw_{tienda}_*.json"))
    if not archivos:
        return f"❌ No se encontraron archivos para la tienda '{tienda}'."

    archivo = archivos[-1]
    return send_file(archivo, as_attachment=True)

@app.route("/cron/generar-cache")
def generar_cache_remoto():
    try:
        from sneakerhunt import generar_cache_estandar_desde_raw
        generar_cache_estandar_desde_raw()
        return "✅ Cache generado correctamente desde archivos RAW"
    except Exception as e:
        return f"❌ Error al generar cache: {e}"

@app.route("/cron/ejecutar-todo")
def ejecutar_todo_remoto():
    try:
        from sneakerhunt import ejecutar_todo
        ejecutar_todo()
        return "✅ Scrap y cache ejecutados correctamente"
    except Exception as e:
        return f"❌ Error en ejecutar_todo: {e}"
