
import logging
from flask import Flask, render_template, request
from product_scraper import get_kicks_products

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route("/", methods=["GET", "POST"])
def index():
    talla = request.form.get("talla", "9.5")
    min_price = float(request.form.get("min_price", 0))
    max_price = float(request.form.get("max_price", 99999))

    logging.info(f"📥 Filtros recibidos - Talla: {talla}, Precio: Q{min_price} - Q{max_price}")
    productos = get_kicks_products(talla, min_price, max_price)
    logging.info(f"🔎 Productos encontrados: {len(productos)}")

    return render_template("index.html", productos=productos, talla=talla, min_price=min_price, max_price=max_price)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
