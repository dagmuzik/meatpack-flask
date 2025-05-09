from flask import Flask, render_template, request
from product_scraper import get_kicks_products
import logging

app = Flask(__name__)

# Configurar logging básico para consola
logging.basicConfig(level=logging.INFO)

@app.route("/", methods=["GET"])
def index():
    talla = request.args.get("talla", "9.5")
    min_price = float(request.args.get("min", 0))
    max_price = float(request.args.get("max", 99999))

    logging.info(f"📥 Filtros recibidos - Talla: {talla}, Precio: Q{min_price} - Q{max_price}")

    productos = get_kicks_products(talla_deseada=talla)

    # Filtrado adicional por precio
    productos_filtrados = [
        p for p in productos
        if min_price <= float(p["precio"].replace("Q", "").replace(",", "")) <= max_price
    ]

    return render_template("index.html", productos=productos_filtrados, talla=talla)

if __name__ == "__main__":
    app.run(debug=True, port=8080)

