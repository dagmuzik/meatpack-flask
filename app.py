from flask import Flask, render_template, request
from sneakerhunt import buscar_todos

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    talla = ''
    productos = None

    if request.method == 'POST':
        talla = request.form.get('talla', '').strip()
        if talla:
            resultados = buscar_todos(talla)
            productos = resultados.to_dict(orient='records') if not resultados.empty else []

    return render_template('index.html', talla=talla, productos=productos)

if __name__ == '__main__':
    app.run(debug=True)
