import os
from flask import Flask, render_template, request
from product_scraper import scrape_kicks_product

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    resultado = None
    mensaje = ""
    if request.method == "POST":
        url = request.form.get("url")
        talla = request.form.get("talla", "9.5")
        if url:
            producto = scrape_kicks_product(url, talla)
            if producto:
                resultado = [producto]  # lo mandamos como lista para renderizar igual
            else:
                mensaje = f"No se encontró la talla {talla} en el producto proporcionado."

    return render_template("index.html",
                           productos=resultado,
                           mensaje=mensaje)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

