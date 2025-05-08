import requests
from bs4 import BeautifulSoup
import json
import logging

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

def get_kicks_products(talla="9.5", min_price=0, max_price=99999):
    logging.info("🔄 Obteniendo productos de KICKS...")
    productos = []
    base_url = "https://www.kicks.com.gt/sale-tienda?p={}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        for pagina in range(1, 10):
            url = base_url.format(pagina)
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, "html.parser")

            items = soup.select(".product-item-info")
            if not items:
                break

            for item in items:
                try:
                    nombre = item.select_one(".product-item-link").text.strip()
                    url_producto = item.select_one(".product-item-link")["href"]
                    imagen = item.select_one(".product-image-photo")["src"]

                    detalle = requests.get(url_producto, headers=headers)
                    soup_detalle = BeautifulSoup(detalle.content, "html.parser")

                    precios = soup_detalle.select(".price")
                    precio = 0
                    for p in precios:
                        try:
                            precio = float(p.text.replace("Q", "").replace(",", "").strip())
                            break
                        except:
                            continue

                    if not (min_price <= precio <= max_price):
                        continue

                    talla_tags = soup_detalle.select("div.swatch-attribute.size div.swatch-option")
                    tallas = [t.get("aria-label").replace("½", ".5").strip() for t in talla_tags]

                    if talla in tallas:
                        productos.append({
                            "nombre": nombre,
                            "precio": precio,
                            "talla": talla,
                            "url": url_producto,
                            "imagen": imagen
                        })
                except Exception as e:
                    logging.warning(f"[KICKS] Producto con error: {e}")
    except Exception as e:
        logging.warning(f"[KICKS] Error al obtener productos: {e}")
    return productos

def get_all_products(talla="9.5", min_price=0, max_price=99999):
    return {
        "Meatpack": get_meatpack_products(talla, min_price, max_price),
        "La Grieta": get_lagrieta_products(talla, min_price, max_price),
        "KICKS": get_kicks_products(talla, min_price, max_price),
        # "Bitterheads": get_bitterheads_products(talla, min_price, max_price)
    }
