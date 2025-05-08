
import requests
from bs4 import BeautifulSoup
import logging
import re

logging.basicConfig(level=logging.INFO)

def detectar_marca(nombre):
    nombre_lower = nombre.lower()
    if "adidas" in nombre_lower:
        return "adidas"
    elif "nike" in nombre_lower:
        return "nike"
    elif "puma" in nombre_lower:
        return "puma"
    elif "reebok" in nombre_lower:
        return "reebok"
    elif "new balance" in nombre_lower or "nb" in nombre_lower:
        return "new balance"
    elif "salomon" in nombre_lower:
        return "salomon"
    elif "converse" in nombre_lower:
        return "converse"
    elif "vans" in nombre_lower:
        return "vans"
    elif "jordan" in nombre_lower:
        return "jordan"
    else:
        return "otro"

def get_meatpack_products(talla_busqueda="9.5", min_price=0, max_price=99999):
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

                if talla == talla_busqueda and disponible and min_price <= precio <= max_price:
                    productos.append({
                        "marca": detectar_marca(nombre),
                        "nombre": nombre,
                        "precio_final": precio,
                        "precio_original": None,
                        "descuento": None,
                        "talla": talla,
                        "tienda": "MEATPACK",
                        "url": url_producto,
                        "imagen": imagen
                    })
    except Exception as e:
        logging.warning(f"[MEATPACK] Error: {e}")

    return productos

def get_lagrieta_products(talla_busqueda="9.5", min_price=0, max_price=99999):
    logging.info("🔄 Obteniendo productos de LA GRIETA...")
    url = "https://lagrieta.gt/collections/ultimas-tallas"
    productos = []

    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        items = soup.select("li.grid__item")

        for item in items:
            nombre_tag = item.select_one("a.full-unstyled-link")
            if not nombre_tag:
                continue

            nombre = nombre_tag.text.strip()
            url_producto = "https://lagrieta.gt" + nombre_tag["href"]
            imagen_tag = item.select_one("img.motion-reduce")
            imagen = imagen_tag["src"].replace("{width}", "800") if imagen_tag else ""
            precio_tag = item.select_one(".price")
            if not precio_tag:
                continue

            try:
                precio = float(precio_tag.text.strip().replace("Q", "").replace(",", ""))
            except:
                continue

            if not (min_price <= precio <= max_price):
                continue

            detalle = requests.get(url_producto)
            soup_detalle = BeautifulSoup(detalle.content, "html.parser")
            tallas = [
                t.get_text(strip=True).replace("½", ".5").replace(" ", "")
                for t in soup_detalle.select("fieldset input + label")
            ]

            if talla_busqueda in tallas:
                productos.append({
                    "marca": detectar_marca(nombre),
                    "nombre": nombre,
                    "precio_final": precio,
                    "precio_original": None,
                    "descuento": None,
                    "talla": talla_busqueda,
                    "tienda": "LA GRIETA",
                    "url": url_producto,
                    "imagen": "https:" + imagen if imagen.startswith("//") else imagen
                })
    except Exception as e:
        logging.warning(f"[LA GRIETA] Error: {e}")

    return productos

def get_kicks_products(talla_filtrada, min_price, max_price):
    import re
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

                # Extraer precio actual
                match = re.search(r"(\d+\.\d+)", precio_texto.replace(",", ""))
                if not match:
                    raise ValueError(f"No se pudo extraer precio de: {precio_texto}")
                precio_final = float(match.group(1))

                if not (min_price <= precio_final <= max_price):
                    continue

                # Obtener página de producto para tallas
                detalle = requests.get(url_producto, headers=headers)
                detalle_soup = BeautifulSoup(detalle.text, "html.parser")
                tallas_tags = detalle_soup.select(".swatch-option.text")
                tallas_disponibles = [
                    t.get_text(strip=True).replace("½", ".5") for t in tallas_tags if "disabled" not in t.get("class", [])
                ]

                if talla_filtrada and talla_filtrada not in tallas_disponibles:
                    continue

                productos.append({
                    "marca": detectar_marca(nombre),
                    "nombre": nombre,
                    "precio_final": precio_final,
                    "precio_original": None,
                    "descuento": None,
                    "talla": talla_filtrada,
                    "tienda": "KICKS",
                    "url": url_producto,
                    "imagen": imagen
                })

            except Exception as e:
                logging.warning(f"[KICKS] Producto con error: {e}")

    except Exception as e:
        logging.error(f"[KICKS] Error general: {e}")

    return productos

def get_all_products(talla, min_price, max_price):
    return {
        "MEATPACK": get_meatpack_products(talla, min_price, max_price),
        "LA GRIETA": get_lagrieta_products(talla, min_price, max_price),
        "KICKS": get_kicks_products(talla, min_price, max_price)
    }
