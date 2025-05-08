import requests
from bs4 import BeautifulSoup
import json
import logging
import re

logging.basicConfig(level=logging.INFO)

def get_meatpack_products(talla="9.5", min_price=0, max_price=99999):
    logging.info("🔄 Obteniendo productos de MEATPACK...")
    url = "https://meatpack.com/collections/special-price/products.json"
    productos = []
    try:
        response = requests.get(url)
        data = response.json()

        for producto in data["products"]:
            nombre = producto["title"]
            handle = producto["handle"]
            imagen = producto["images"][0] if producto["images"] else ""
            url_producto = f"https://meatpack.com/products/{handle}"

            for variante in producto.get("variants", []):
                talla = variante["option1"]
                disponible = variante["available"]
                precio = float(variante["price"])
                if precio > 1000:
                    precio = precio / 100

                if talla and disponible and min_price <= precio <= max_price and talla == talla:
                    productos.append({
                        "nombre": nombre,
                        "precio": precio,
                        "talla": talla,
                        "url": url_producto,
                        "imagen": imagen
                    })
    except Exception as e:
        logging.warning(f"[MEATPACK] Error al obtener productos: {e}")
    return productos

def get_lagrieta_products(talla="9.5", min_price=0, max_price=99999):
    logging.info("🔄 Obteniendo productos de LA GRIETA...")
    url = "https://lagrieta.gt/collections/ultimas-tallas"
    productos = []
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        items = soup.select("li.grid__item")

        for item in items:
            nombre = item.select_one("a.full-unstyled-link").text.strip()
            url_producto = "https://lagrieta.gt" + item.select_one("a.full-unstyled-link")["href"]
            imagen = item.select_one("img.motion-reduce")["src"].replace("{width}", "800")
            precio_texto = item.select_one(".price").text.strip().replace("Q", "").replace(",", "")
            try:
                precio = float(precio_texto)
            except:
                precio = 0

            if not (min_price <= precio <= max_price):
                continue

            detalle = requests.get(url_producto)
            soup_detalle = BeautifulSoup(detalle.content, "html.parser")
            tallas = [t.get_text(strip=True).replace("½", ".5").replace(" ", "") for t in soup_detalle.select("fieldset input + label")]

            if talla in tallas:
                productos.append({
                    "nombre": nombre,
                    "precio": precio,
                    "talla": talla,
                    "url": url_producto,
                    "imagen": "https:" + imagen if imagen.startswith("//") else imagen
                })
    except Exception as e:
        logging.warning(f"[LA GRIETA] Error al obtener productos: {e}")
    return productos

def get_kicks_products(talla_filtrada, min_price, max_price):
    print("🔄 Obteniendo productos de KICKS...")
    url = "https://www.kicks.com.gt/sale-tienda"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    productos = []

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.select(".product-item-info")

        for item in items:
            try:
                link_tag = item.select_one("a.product.photo.product-item-photo")
                if not link_tag:
                    continue

                url_producto = link_tag["href"]
                nombre_tag = item.select_one(".product.name.product-item-name a")
                precio_tag = item.select_one(".price")
                if not nombre_tag or not precio_tag:
                    continue

                nombre = nombre_tag.get_text(strip=True)
                imagen_tag = item.select_one(".product-image-photo")
                imagen = imagen_tag["src"] if imagen_tag else ""
                precio_texto = precio_tag.get_text(strip=True)

                match = re.search(r"(\d+\.\d+)", precio_texto.replace(",", ""))
                if not match:
                    raise ValueError(f"No se pudo extraer precio de: {precio_texto}")
                precio = float(match.group(1))

                if not (min_price <= precio <= max_price):
                    continue

                detalle = requests.get(url_producto, headers=headers)
                detalle_soup = BeautifulSoup(detalle.text, "html.parser")
                tallas_tags = detalle_soup.select(".swatch-option.text")

                tallas_disponibles = [
                    t.get_text(strip=True).replace("½", ".5")
                    for t in tallas_tags
                    if "disabled" not in t.get("class", [])
                ]

                if talla_filtrada and talla_filtrada not in tallas_disponibles:
                    continue

                productos.append({
                    "nombre": nombre,
                    "precio_final": precio,
                    "precio_original": None,
                    "descuento": None,
                    "url": url_producto,
                    "imagen": imagen,
                    "talla": talla_filtrada,
                })

            except Exception as e:
                logging.warning(f"[KICKS] Producto con error: {e}")

    except Exception as e:
        logging.error(f"[KICKS] Error general: {e}")

    return productos

def get_all_products(talla="9.5", min_price=0, max_price=99999):
    return {
        "Meatpack": get_meatpack_products(talla, min_price, max_price),
        "La Grieta": get_lagrieta_products(talla, min_price, max_price),
        "KICKS": get_kicks_products(talla, min_price, max_price),
        # "Bitterheads": get_bitterheads_products(talla, min_price, max_price)
    }
