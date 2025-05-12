from flask import Flask, render_template, request
from sneakerhunt import buscar_todos

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    productos = None
    talla = ""
    tienda = ""

    if request.method == "POST":
        talla = request.form.get("talla", "").strip()
        tienda = request.form.get("tienda", "").strip()
        if talla:
            print(f"🔎 Buscando productos talla {talla} en tienda: {tienda or 'Todas'}")
            productos = buscar_todos(talla, tienda)
        else:
            productos = []

    return render_template("index.html", productos=productos, talla=talla, tienda=tienda)

if __name__ == "__main__":
    app.run(debug=True)
