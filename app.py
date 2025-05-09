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

    # 🔁 Unificamos todos los productos en una lista y agregamos la tienda a cada uno
    productos_totales = []
    for tienda, lista in productos_por_tienda.items():
        for p in lista:
            p["tienda"] = tienda
            productos_totales.append(p)

    # 🔽 Ordenamos por precio final
        productos_ordenados = sorted(
        [p for p in productos_totales if "precio_final" in p and p["precio_final"] is not None],
        key=lambda x: x["precio_final"]
    )

    return render_template("index.html",
                           productos=productos_ordenados,
                           talla=talla,
                           min_price=min_price,
                           max_price=max_price)

