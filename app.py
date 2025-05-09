# app.py (con logs para debug)
from flask import Flask, render_template, request
from product_scraper import get_kicks_products
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route("/", methods=["GET", "POST"])
def index():
    talla = request.values.get("talla", "9")
    try:
        min_price = float(request.values.get("min_price") or 0)
    except ValueError:
        min_price = 0
    try:
        max_price = float(request.values.get("max_price") or 99999)
    except ValueError:
        max_price = 99999

    logging.info(f"📥 Filtros recibidos - Talla: {talla}, Precio: Q{min_price} - Q{max_price}")

    productos = get_kicks_products(talla, min_price, max_price)
    logging.info(f"🔎 Productos encontrados: {len(productos)}")

    productos = [p for p in productos if "precio_final" in p and p["precio_final"] is not None]
    productos_ordenados = sorted(productos, key=lambda x: x["precio_final"])

    for p in productos_ordenados:
        logging.info(f"✅ {p['nombre']} - Q{p['precio_final']} - Tallas: {p.get('tallas_disponibles', 'N/A')}")

    return render_template("index.html", productos=productos_ordenados, talla=talla, min_price=min_price, max_price=max_price)

if __name__ == "__main__":
    app.run(debug=True)
