import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
import logging
logging.basicConfig(level=logging.INFO)

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
    tienda = "Meatpack"

    for producto in data.get("products", []):
        nombre = producto["title"]
        handle = producto["handle"]
        url = f"https://meatpack.com/products/{handle}"
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

def get_kicks_products(talla_busqueda, min_price, max_price):
    base_url = "https://www.kicks.com.gt"
    listing_url = f"{base_url}/collections/sale?page=1"
    response = requests.get(listing_url)
    soup = BeautifulSoup(response.text, "html.parser")

    products = []
    product_links = list(set(a["href"] for a in soup.select("a.product-item-link") if a.get("href")))

    for link in product_links:
        full_url = base_url + link if link.startswith("/") else link
        res = requests.get(full_url)
        prod_soup = BeautifulSoup(res.text, "html.parser")
        script_tag = prod_soup.find("script", type="text/x-magento-init")

        title = prod_soup.find("h1", class_="page-title").get_text(strip=True) if prod_soup.find("h1", class_="page-title") else "No Title"
        price = prod_soup.select_one("span.price")
        price = price.get_text(strip=True) if price else "N/A"
        image_tag = prod_soup.select_one("img.fotorama__img")
        image_url = image_tag["src"] if image_tag else ""

        tallas_disponibles = []
        if script_tag:
            try:
                match = re.search(r'"jsonConfig"\s*:\s*({.*?"attributes".*?})\s*,\s*"template"', script_tag.text, re.DOTALL)
                match_simple = re.search(r'window.simpleProducts\s*=\s*({.*?});', res.text, re.DOTALL)

                if match:
                    config_json = match.group(1)
                    config = json.loads(config_json)

                    disponibles = set()
                    if match_simple:
                        data = json.loads(match_simple.group(1))
                        disponibles = {str(item["id"]) for item in data.get("lines", [])}

                    for attr in config["attributes"].values():
                        for option in attr["options"]:
                            talla = option["label"]
                            ids = option.get("products", [])
                            disponible = any(pid in disponibles for pid in ids)
                            if disponible and talla_busqueda in talla:
                                tallas_disponibles.append(talla)
            except Exception as e:
                print(f"⚠️ Error al procesar tallas en {full_url}: {e}")

        products.append({
            "title": title,
            "price": price,
            "url": full_url,
            "image": image_url,
            "tallas_disponibles": tallas_disponibles,
            "fecha": datetime.now().strftime("%Y-%m-%d")
        })

    return products

def get_all_products(talla="9.5", min_price=0, max_price=99999):
    return {
        "Meatpack": get_meatpack_products(talla, min_price, max_price),
        "La Grieta": get_lagrieta_products(talla, min_price, max_price),
        "KICKS": get_kicks_products(talla, min_price, max_price)
    }
