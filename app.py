from flask import Flask, render_template, request
from product_scraper import get_all_products

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    talla = "9.5"
    min_price = 0
    max_price = 99999

    if request.method == "POST":
        talla = request.form.get("talla", "9.5")
        try:
            min_price = float(request.form.get("min_price") or 0)
        except ValueError:
            min_price = 0
        try:
            max_price = float(request.form.get("max_price") or 99999)
        except ValueError:
            max_price = 99999

    productos_por_tienda = get_all_products(talla, min_price, max_price)
    return render_template("index.html", productos_por_tienda=productos_por_tienda, talla=talla, min_price=min_price, max_price=max_price)

if __name__ == "__main__":
    app.run(debug=True)
