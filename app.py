from flask import Flask, render_template, request
from sneakerhunt import buscar_todos

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    talla = request.values.get('talla', '9.5')
    
    resultados = buscar_todos(talla)

    productos = resultados.to_dict(orient='records')

    return render_template('index.html', productos=productos, talla=talla)

if __name__ == '__main__':
    app.run(debug=True)
