from flask import Flask, request, render_template
from product_scraper import get_kicks_products
import logging

app = Flask(__name__)

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),                   # Consola
        logging.FileHandler('kicks_scraper.log')   # Archivo
    ]
)

@app.route('/')
def index():
    talla = request.args.get('talla', default='9.5')
    min_price = float(request.args.get('min_price', 0))
    max_price = float(request.args.get('max_price', 99999))

    logging.info(f"📥 Filtros recibidos - Talla: {talla}, Precio: Q{min_price} - Q{max_price}")

    try:
        productos = get_kicks_products(talla_filtro=talla, min_precio=min_price, max_precio=max_price)
    except Exception as e:
        logging.error("❌ Error en get_kicks_products", exc_info=True)
        productos = []

    return render_template('index.html', productos=productos, talla=talla)

if __name__ == '__main__':
    app.run(debug=True)
