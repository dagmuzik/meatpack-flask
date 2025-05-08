import requests
from bs4 import BeautifulSoup
import time

KNOWN_BRANDS = [
    "Nike", "Adidas", "Puma", "New Balance", "Vans", "Reebok",
    "Converse", "Under Armour", "Asics", "Saucony", "Salomon",
    "Jordan", "Mizuno", "Fila", "Hoka", "On"
]

def detectar_marca(nombre):
    nombre_lower = nombre.lower()
    for marca in KNOWN_BRANDS:
        if marca.lower() in nombre_lower:
            return marca
    return nombre.split()[0]

def get_meatpack_products(talla_busqueda, min_price, max_price):
    URL = "https://meatpack.com/collections/special-price/products.json"
    response = requests.get(URL)
    data = response.json()
    productos = []

    for producto in data.get("products", []):
        nombre = producto["title"]
        handle = producto["handle"]
        url = f"https://meatpack.com/products/{handle}"
        tienda = "Meatpack"
        marca = detectar_marca(nombre)
        imagen = producto["images"][0]["src"] if producto.get("images") else ""

        for variante in producto.get("variants", []):
            talla = variante["option1"]
            disponible = variante["available"]
            precio_raw = float(variante["price"])
            precio = precio_raw / 100 if precio_raw % 100 == 0 else precio_raw

            compare_at_raw = variante.get("compare_at_price")
            if compare_at_raw:
                compare_at_raw = float(compare_at_raw)
                compare_at = compare_at_raw / 100 if compare_at_raw % 100 == 0 else compare_at_raw
            else:
                compare_at = None

            if talla_busqueda in talla and disponible and min_price <= precio <= max_price:
                descuento = ""
                if compare_at and compare_at > precio:
                    descuento = f"{round((compare_at - precio) / compare_at * 100)}%"

                productos.append({
                    "marca": marca,
                    "nombre": nombre,
                    "precio_final": precio,
                    "precio_original": compare_at,
                    "descuento": descuento,
                    "talla": talla,
                    "tienda": tienda,
                    "url": url,
                    "imagen": imagen
                })

    return sorted(productos, key=lambda x: x["precio_final"])

def get_lagrieta_products(talla_busqueda, min_price, max_price):
    URL = "https://lagrieta.gt/collections/ultimas-tallas/products.json"
    response = requests.get(URL)
    data = response.json()
    productos = []
    tienda = "La Grieta"

    for producto in data["products"]:
        nombre = producto["title"]
        handle = producto["handle"]
        url = f"https://lagrieta.gt/products/{handle}"
        marca = detectar_marca(nombre)
        imagen = producto["images"][0]["src"] if producto.get("images") else ""

        for variante in producto["variants"]:
            talla = variante["title"]
            disponible = variante["available"]
            try:
                precio = float(variante["price"])
            except:
                precio = None

            if talla_busqueda in talla and disponible and precio is not None and min_price <= precio <= max_price:
                productos.append({
                    "marca": marca,
                    "nombre": nombre,
                    "precio_final": precio,
                    "precio_original": None,
                    "descuento": "",
                    "talla": talla,
                    "tienda": tienda,
                    "url": url,
                    "imagen": imagen
                })

    return sorted(productos, key=lambda x: x["precio_final"])

import logging
logging.basicConfig(level=logging.INFO)

def get_bitterheads_products(talla_busqueda, min_price, max_price):
    url = "https://www.bitterheads.com/collections/sneakers"
    productos = []
    tienda = "Bitterheads"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []
    except:
        return []

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")
    items = soup.select(".productgrid--item")

    for item in items:
        nombre_tag = item.select_one(".productitem--title")
        url_tag = item.select_one("a")
        precio_tag = item.select_one(".price__current")
        talla_tag = item.select_one(".productitem--variants")
        imagen_tag = item.select_one("img")

        if not all([nombre_tag, url_tag, precio_tag, talla_tag]):
            continue

        nombre = nombre_tag.get_text(strip=True)
        link = "https://www.bitterheads.com" + url_tag["href"]
        imagen = imagen_tag["src"] if imagen_tag else ""

        logging.info(f"➡️ Producto: {nombre}")
        logging.info(f"➡️ Tallas crudas: {talla_tag.get_text(strip=True)}")
        logging.info(f"➡️ URL: {link}")

        try:
            precio = float(precio_tag.get_text(strip=True).replace("Q", "").replace(",", ""))
        except:
            continue

        tallas = [
            t.strip().replace("½", ".5").replace(" ", "")
            for t in talla_tag.get_text(strip=True).lower().replace("talla:", "").replace("|", "/").split("/")
            if t.strip()
        ]
        talla_input_normalizada = talla_busqueda.strip().replace(".", "").replace(" ", "")

        if any(t.replace(".", "") == talla_input_normalizada for t in tallas) and min_price <= precio <= max_price:
            productos.append({
                "marca": nombre.split()[0],
                "nombre": nombre,
                "precio_final": precio,
                "precio_original": None,
                "descuento": "",
                "talla": talla_busqueda,
                "tienda": tienda,
                "url": link,
                "imagen": imagen
            })

    return sorted(productos, key=lambda x: x["precio_final"])

def get_all_products(talla="9.5", min_price=0, max_price=99999):
    return {
        "Meatpack": get_meatpack_products(talla, min_price, max_price),
        "La Grieta": get_lagrieta_products(talla, min_price, max_price),
        "Bitterheads": get_bitterheads_products(talla, min_price, max_price)
    }
