# app.py
from flask import Flask, render_template, request
from product_scraper import get_kicks_products

app = Flask(__name__)

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

    productos = get_kicks_products(talla, min_price, max_price)
    productos = [p for p in productos if "precio_final" in p and p["precio_final"] is not None]
    productos_ordenados = sorted(productos, key=lambda x: x["precio_final"])

    return render_template("index.html", productos=productos_ordenados, talla=talla, min_price=min_price, max_price=max_price)

if __name__ == "__main__":
    app.run(debug=True)
