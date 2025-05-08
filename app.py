from flask import Flask, render_template, request
from meatpack_scraper import get_products

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    talla = "9.5"
    productos = []
    if request.method == "POST":
        talla = request.form.get("talla", "9.5")
        productos = get_products(talla)
    return render_template("index.html", productos=productos, talla=talla)
