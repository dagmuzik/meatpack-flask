import os
from flask import Flask, render_template, request
from product_scraper import get_all_products

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

    productos_por_tienda = get_all_products(talla, min_price, max_price)

    productos_totales = []
    for tienda, lista in productos_por_tienda.items():
        for p in lista:
            p["tienda"] = tienda
            productos_totales.append(p)

    productos_ordenados = sorted(productos_totales, key=lambda x: x["precio_final"])

    return render_template("index.html",
                           productos=productos_ordenados,
                           talla=talla,
                           min_price=min_price,
                           max_price=max_price)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

