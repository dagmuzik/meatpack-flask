from flask import Flask, render_template, request
from sneakerhunt import buscar_todos

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    productos = None
    talla = ""
    tienda = ""
    marca = ""
    genero = ""

    if request.method == "POST":
        talla = request.form.get("talla", "").strip()
        tienda = request.form.get("tienda", "").strip()
        marca = request.form.get("marca", "").strip()
        genero = request.form.get("genero", "").strip()
        productos = buscar_todos(talla=talla, tienda=tienda, marca=marca, genero=genero)

    return render_template("index.html", productos=productos, talla=talla, tienda=tienda, marca=marca, genero=genero)

if __name__ == "__main__":
    app.run(debug=True)
