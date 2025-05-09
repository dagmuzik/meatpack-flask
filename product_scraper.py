# product_scraper.py
import logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# Configurar logger
logger = logging.getLogger('kicks_scraper')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

file_handler = logging.FileHandler(f'kicks_scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def get_kicks_products(talla_filtro="9.5", min_precio=0.0, max_precio=99999.0):
    logger.info("Iniciando scraping de Kicks")
    base_url = "https://www.kicks.com.gt"
    collection_url = f"{base_url}/calzado.html?p={{}}"

    productos = []

    for page in range(1, 4):
        url = collection_url.format(page)
        logger.info(f"Procesando página {page}: {url}")

        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
        except Exception as e:
            logger.error(f"Error cargando {url}: {e}")
            continue

        soup = BeautifulSoup(r.text, "html.parser")
        enlaces = soup.select(".product-item-info a.product.photo")

        logger.info(f"{len(enlaces)} productos encontrados en la página.")

        for enlace in enlaces:
            product_url = enlace.get("href")
            logger.debug(f"🔍 Consultando producto: {product_url}")
            try:
                pr = requests.get(product_url, timeout=10)
                pr.raise_for_status()
                psoup = BeautifulSoup(pr.text, "html.parser")

                tallas = [div.get("aria-label") for div in psoup.select(".swatch-option") if div.get("aria-label")]
                logger.debug(f"Tallas disponibles: {tallas}")

                if talla_filtro in tallas:
                    nombre_elem = psoup.select_one("h1.page-title span")
                    precio_elem = psoup.select_one("span.price")

                    if nombre_elem and precio_elem:
                        nombre = nombre_elem.text.strip()
                        precio_str = precio_elem.text.strip().replace("Q", "").replace(",", "").strip()
                        try:
                            precio = float(precio_str)
                        except ValueError:
                            logger.warning(f"Precio no válido '{precio_str}' para {product_url}")
                            continue

                        if min_precio <= precio <= max_precio:
                            productos.append({
                                "nombre": nombre,
                                "precio": f"Q{precio:.2f}",
                                "url": product_url,
                                "tienda": "Kicks"
                            })
                            logger.info(f"✅ Producto válido: {nombre} - Q{precio:.2f}")
            except Exception as e:
                logger.error(f"❌ Error procesando {product_url}: {e}")

    logger.info(f"🎯 Total productos encontrados: {len(productos)}")
    return productos

# Para prueba CLI directa
if __name__ == "__main__":
    resultados = get_kicks_products(talla_filtro="9.5", min_precio=0, max_precio=99999)
    print("\n🎯 Productos encontrados:")
    for p in resultados:
        print(f"- {p['nombre']} ({p['precio']}) - {p['url']}")

