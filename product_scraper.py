import requests
from bs4 import BeautifulSoup
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

def get_product_details(url_producto):
    """Scrapea la página del producto individual de KICKS para extraer tallas disponibles."""
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url_producto, headers=headers, timeout=10)
        if response.status_code != 200:
            logging.warning(f"⚠️ Producto no disponible: {url_producto}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        tallas = []
        talla_tags = soup.select(".swatch-attribute.size .swatch-option.text")

        for tag in talla_tags:
            if tag.get("aria-disabled") != "true":
                tallas.append(tag.get("option-label") or tag.text.strip())

        logging.info(f"🔎 Tallas extraídas de {url_producto}: {tallas}")
        return tallas

    except Exception as e:
        logging.error(f"💥 Error en get_product_details({url_producto}): {e}")
        return []

def get_kicks_products(talla_busqueda, min_price, max_price):
    url = "https://www.kicks.com.gt/sale-tienda"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    productos = []
    tienda = "KICKS"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logging.warning(f"❌ KICKS no respondió correctamente: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.select(".product-item-info")

        for item in items:
            nombre = item.select_one(".product-item-name").text.strip() if item.select_one(".product-item-name") else "Sin nombre"
            href = item.select_one("a")["href"]
            url_producto = href if href.startswith("http") else f"https://www.kicks.com.gt{href}"
            imagen = item.select_one("img")["src"] if item.select_one("img") else ""
            precio_final_tag = item.select_one(".special-price .price") or item.select_one(".price")
            precio_original_tag = item.select_one(".old-price .price")

            try:
                precio_final = float(precio_final_tag.text.replace("Q", "").replace(",", "").strip())
            except:
                precio_final = 0.0

            if precio_original_tag:
                try:
                    precio_original = float(precio_original_tag.text.replace("Q", "").replace(",", "").strip())
                except:
                    precio_original = precio_final
            else:
                precio_original = precio_final

            if not (min_price <= precio_final <= max_price):
                continue

            tallas_disponibles = get_product_details(url_producto)

            if talla_busqueda not in tallas_disponibles:
                continue

            descuento = ""
            if precio_original > precio_final:
                descuento = f"-{round((1 - (precio_final / precio_original)) * 100)}%"

            productos.append({
                "marca": detectar_marca(nombre),
                "nombre": nombre,
                "precio_final": precio_final,
                "precio_original": precio_original,
                "descuento": descuento,
                "talla": talla_busqueda,
                "tienda": tienda,
                "url": url_producto,
                "imagen": imagen
            })

        logging.info(f"🟢 KICKS productos encontrados: {len(productos)}")
        return productos

    except Exception as e:
        logging.error(f"💥 Error en get_kicks_products: {e}")
        return []

def get_all_products(talla="9.5", min_price=0, max_price=99999):
    return {
        "Meatpack": get_meatpack_products(talla, min_price, max_price),
        "La Grieta": get_lagrieta_products(talla, min_price, max_price),
        "KICKS": get_kicks_products(talla, min_price, max_price)
        # "Bitterheads": get_bitterheads_products(talla, min_price, max_price),  # se puede reactivar cuando esté listo
    }
