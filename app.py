from flask import Flask, render_template, request
from sneakerhunt import buscar_todos, obtener_ultimo_cache_tienda
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
        ejecutar_todo()
        return "✅ Scraper ejecutado correctamente desde cron"
    except Exception as e:
        return f"❌ Error al ejecutar scraper: {e}"


@app.route("/cron/ejecutar-todo")
def ejecutar_todo_remoto():
    try:
        from sneakerhunt import ejecutar_todo
        ejecutar_todo()
        return "✅ Scrap y cache ejecutados correctamente"
    except Exception as e:
        return f"❌ Error en ejecutar_todo: {e}"


@app.route("/descargar-cache")
def descargar_cache():
    tienda = request.args.get("tienda", "").lower()
    if not tienda:
        return "❌ Debes especificar una tienda con ?tienda=meatpack, lagrieta o adidas"

    archivo = obtener_ultimo_cache_tienda(tienda)
    if not archivo or not os.path.exists(archivo):
        return f"❌ No se encontró archivo cache para '{tienda}'"

    return send_file(archivo, as_attachment=True)
