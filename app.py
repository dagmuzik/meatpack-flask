from flask import Flask, render_template, request
from sneakerhunt import buscar_todos

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    productos = None
    talla = ""
    tienda = ""
    marca = ""

    if request.method == "POST":
        talla = request.form.get("talla", "").strip()
        tienda = request.form.get("tienda", "").strip()
        marca = request.form.get("marca", "").strip()

        try:
            productos = buscar_todos(talla=talla, tienda=tienda, marca=marca)
        except Exception as e:
            print("❌ Error en búsqueda:", str(e))
            productos = []

    return render_template("index.html", productos=productos, talla=talla, tienda=tienda, marca=marca)

if __name__ == "__main__":
    app.run(debug=True)