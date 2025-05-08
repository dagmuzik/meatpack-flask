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

def get_kicks_products(talla, min_price, max_price):
    print("🔄 Obteniendo productos de KICKS...")
    url = "https://www.kicks.com.gt/sale-tienda"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[KICKS] Error al obtener la página principal: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    productos = []

    items = soup.select(".product-item-info")

    for item in items:
        try:
            nombre = item.select_one(".product-item-name").get_text(strip=True)
            precio_tag = item.select_one(".price")
            precio = float(precio_tag.get_text(strip=True).replace("Q", "").replace(",", "").strip())

            # Enlace corregido
            partial_url = item.select_one(".product-item-link")["href"]
            if not partial_url.startswith("http"):
                url_producto = "https://www.kicks.com.gt" + partial_url
            else:
                url_producto = partial_url

            # Obtener imagen
            imagen_tag = item.select_one(".product-image-photo")
            imagen_url = imagen_tag["src"] if imagen_tag else ""

            # Obtener tallas desde la página del producto
            detalle = requests.get(url_producto, headers=headers, timeout=10)
            detalle.raise_for_status()
            detalle_soup = BeautifulSoup(detalle.text, "html.parser")
            talla_tags = detalle_soup.select(".swatch-option.text")

            tallas_disponibles = [t.get_text(strip=True).replace("½", ".5").replace(" ", "") for t in talla_tags]

            if not talla or talla in tallas_disponibles:
                if min_price <= precio <= max_price:
                    productos.append({
                        "nombre": nombre,
                        "precio": precio,
                        "url": url_producto,
                        "imagen": imagen_url,
                        "tallas": tallas_disponibles
                    })

        except Exception as e:
            print(f"[KICKS] Producto con error: {e}")
            continue

    return productos

def get_all_products(talla="9.5", min_price=0, max_price=99999):
    return {
        "Meatpack": get_meatpack_products(talla, min_price, max_price),
        "La Grieta": get_lagrieta_products(talla, min_price, max_price),
        "KICKS": get_kicks_products(talla, min_price, max_price),
        # "Bitterheads": get_bitterheads_products(talla, min_price, max_price)
    }
