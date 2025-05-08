import requests
from bs4 import BeautifulSoup
import logging
import re

def detectar_marca(nombre):
    nombre_lower = nombre.lower()
    if "nike" in nombre_lower:
        return "Nike"
    elif "adidas" in nombre_lower:
        return "Adidas"
    elif "new balance" in nombre_lower or "nb" in nombre_lower:
        return "New Balance"
    elif "puma" in nombre_lower:
        return "Puma"
    elif "jordan" in nombre_lower:
        return "Jordan"
    elif "reebok" in nombre_lower:
        return "Reebok"
    else:
        return "Otra"

def get_meatpack_products(talla_busqueda, min_price, max_price):
    print("🔄 Obteniendo productos de MEATPACK...")
    url = "https://meatpack.com/collections/special-price/products.json"
    productos = []

    try:
        response = requests.get(url)
        data = response.json()

        for producto in data["products"]:
            nombre = producto["title"]
            url_producto = f'https://meatpack.com/products/{producto["handle"]}'
            imagen = producto["images"][0] if producto["images"] else ""
            variantes = producto["variants"]

            precio_original = variantes[0]["compare_at_price"]
            precio_final = variantes[0]["price"]

            try:
                precio_original = float(precio_original)
                precio_final = float(precio_final)
                descuento = round(100 - (precio_final / precio_original * 100)) if precio_original else 0
            except:
                continue

            if not (min_price <= precio_final <= max_price):
                continue

            for variante in variantes:
                talla = variante["title"]
                if talla_busqueda.lower() not in talla.lower():
                    continue

                productos.append({
                    "marca": detectar_marca(nombre),
                    "nombre": nombre,
                    "precio_final": precio_final,
                    "precio_original": precio_original,
                    "descuento": descuento,
                    "talla": talla,
                    "tienda": "Meatpack",
                    "url": url_producto,
                    "imagen": imagen
                })
    except Exception as e:
        logging.error(f"[MEATPACK] Error general: {e}")

    return productos

def get_lagrieta_products(talla_busqueda, min_price, max_price):
    print("🔄 Obteniendo productos de LA GRIETA...")
    url = "https://lagrieta.gt/collections/ultimas-tallas/products.json"
    productos = []

    try:
        response = requests.get(url)
        data = response.json()

        for producto in data["products"]:
            nombre = producto["title"]
            url_producto = f'https://lagrieta.gt/products/{producto["handle"]}'
            imagen = producto["images"][0] if producto["images"] else ""
            variantes = producto["variants"]

            precio_final = float(variantes[0]["price"])
            precio_original = float(variantes[0].get("compare_at_price") or 0)
            descuento = round(100 - (precio_final / precio_original * 100)) if precio_original else 0

            if not (min_price <= precio_final <= max_price):
                continue

            for variante in variantes:
                talla = variante["title"]
                if talla_busqueda.lower() not in talla.lower():
                    continue

                productos.append({
                    "marca": detectar_marca(nombre),
                    "nombre": nombre,
                    "precio_final": precio_final,
                    "precio_original": precio_original,
                    "descuento": descuento,
                    "talla": talla,
                    "tienda": "La Grieta",
                    "url": url_producto,
                    "imagen": imagen
                })

    except Exception as e:
        logging.error(f"[LA GRIETA] Error general: {e}")

    return productos

def get_kicks_products(talla_filtrada, min_price, max_price):
    print("🔄 Obteniendo productos de KICKS...")
    url = "https://www.kicks.com.gt/sale-tienda"
    headers = {"User-Agent": "Mozilla/5.0"}
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
                    for t in tallas_tags if "disabled" not in t.get("class", [])
                ]

                if talla_filtrada and talla_filtrada not in tallas_disponibles:
                    continue

                productos.append({
                    "marca": detectar_marca(nombre),
                    "nombre": nombre,
                    "precio_final": precio,
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
        "Meatpack": get_meatpack_products(talla, min_price, max_price),
        "La Grieta": get_lagrieta_products(talla, min_price, max_price),
        "KICKS": get_kicks_products(talla, min_price, max_price),
    }
