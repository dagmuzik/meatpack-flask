from flask import Flask, render_template, request
from product_scraper import get_all_products

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    talla = "9.5"
    productos_por_tienda = {}
    if request.method == "POST":
        talla = request.form.get("talla", "9.5")
    
    productos_por_tienda = get_all_products(talla)
    return render_template("index.html", productos_por_tienda=productos_por_tienda, talla=talla)

