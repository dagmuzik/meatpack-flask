from flask import Flask, render_template, request, send_file
from search import buscar_todos, ejecutar_todo
from utils import obtener_ultimos_nuevos, obtener_ultimo_cache_tienda
import glob
import os
import json

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    talla = request.values.get("talla", "").strip()
    tienda = request.values.get("tienda", "").strip()
    marca = request.values.get("marca", "").strip()
    genero = request.values.get("genero", "").strip()

    print(f"🎯 FILTROS => talla: {talla}, tienda: {tienda}, marca: {marca}, genero: {genero}")

    productos = buscar_todos(talla=talla, tienda=tienda, marca=marca, genero=genero)
    nuevos = obtener_ultimos_nuevos()

    return render_template("index.html",
                           productos=productos,
                           talla=talla,
                           tienda=tienda,
                           marca=marca,
                           genero=genero,
                           nuevos=nuevos)


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

@app.route("/descargar-cache-total")
def descargar_cache_total():
    archivos = sorted(glob.glob("data/cache_TOTAL_*.json"))
    if not archivos:
        return "❌ No se encontró ningún archivo cache_TOTAL_*.json"

    ultimo = archivos[-1]
    if not os.path.exists(ultimo):
        return f"❌ Archivo no encontrado: {ultimo}"

    return send_file(ultimo, as_attachment=True)

