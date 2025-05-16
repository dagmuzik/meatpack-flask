from flask import Flask, render_template, request
from product_scraper import get_all_products
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
    talla = request.values.get("talla", "9.5")
    try:
        min_price = float(request.values.get("min_price") or 0)
    except ValueError:
        min_price = 0
    try:
        max_price = float(request.values.get("max_price") or 99999)
    except ValueError:
        max_price = 99999

    productos_por_tienda = get_all_products(talla, min_price, max_price)

    productos_totales = []
    for tienda, lista in productos_por_tienda.items():
        for p in lista:
            p["tienda"] = tienda
            productos_totales.append(p)

    productos_ordenados = sorted(productos_totales, key=lambda x: x["precio_final"])

    nuevos_productos = obtener_ultimos_nuevos()

    return render_template("index.html",
                           productos=productos_ordenados,
                           talla=talla,
                           min_price=min_price,
                           max_price=max_price,
                           nuevos=nuevos_productos)

# ✅ Ruta para ejecutar el scraping desde cron
@app.route("/cron/ejecutar-scraper")
def ejecutar_scraper_remoto():
    try:
        from sneakerhunt import ejecutar_scraping_general
        ejecutar_scraping_general()
        return "✅ Scraper ejecutado correctamente desde cron"
    except Exception as e:
        return f"❌ Error al ejecutar scraper: {e}"
