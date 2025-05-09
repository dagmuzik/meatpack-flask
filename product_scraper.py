# product_scraper.py
import logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# Configurar logger
logger = logging.getLogger('kicks_scraper')
logger.setLevel(logging.DEBUG)

# Handlers: consola + archivo
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

file_handler = logging.FileHandler(f'kicks_scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def get_kicks_products(talla_deseada="9.5"):
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
            logger.debug(f"Consultando producto: {product_url}")
            try:
                pr = requests.get(product_url, timeout=10)
                pr.raise_for_status()
                psoup = BeautifulSoup(pr.text, "html.parser")

                tallas = [div.get("aria-label") for div in psoup.select(".swatch-option") if div.get("aria-label")]

                logger.debug(f"Tallas encontradas: {tallas}")

                if talla_deseada in tallas:
                    nombre = psoup.select_one("h1.page-title span").text.strip()
                    precio = psoup.select_one("span.price").text.strip()
                    productos.append({
                        "nombre": nombre,
                        "precio": precio,
                        "url": product_url
                    })
                    logger.info(f"✅ Producto encontrado: {nombre} - {precio}")
            except Exception as e:
                logger.error(f"Error procesando {product_url}: {e}")

    return productos

if __name__ == "__main__":
    resultados = get_kicks_products("9.5")
    print("\n🎯 Productos encontrados:")
    for p in resultados:
        print(f"- {p['nombre']} ({p['precio']}) - {p['url']}")
