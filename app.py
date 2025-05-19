from flask import Flask, render_template, request
import json
import glob
import os
from scraping_tiendas import (
    obtener_meatpack,
    obtener_lagrieta,
    obtener_adidas_estandarizado,
    obtener_kicks,
    obtener_bitterheads,
    obtener_premiumtrendy,
    obtener_veinteavenida,
    obtener_deportesdelcentro
)
from utils import guardar_en_cache_local
from search import buscar_todos
from utils import obtener_ultimos_nuevos

app = Flask(__name__)

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


from flask import send_file
import glob
import os

@app.route("/descargar-cache-total")
def descargar_cache_total():
    archivos = sorted(glob.glob("data/cache_TOTAL_*.json"))
    if not archivos:
        return "❌ No se encontró ningún archivo cache_TOTAL_*.json"

    ultimo = archivos[-1]
    if not os.path.exists(ultimo):
        return f"❌ Archivo no encontrado: {ultimo}"

    return send_file(ultimo, as_attachment=True)

