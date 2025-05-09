from flask import Flask, render_template, request
from product_scraper import get_kicks_products
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route("/", methods=["GET"])
def index():
    talla = request.args.get("talla", "9")
    try:
        min_price = float(request.args.get("min_price", 0))
        max_price = float(request.args.get("max_price", 99999))
    except ValueError:
        min_price = 0
        max_price = 99999

    logging.info(f"📥 Filtros recibidos - Talla: {talla}, Precio: Q{min_price} - Q{max_price}")
    productos = get_kicks_products(talla=talla, min_precio=min_price, max_precio=max_price)
    
    return render_template("index.html", productos=productos, talla=talla, min_price=min_price, max_price=max_price)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
