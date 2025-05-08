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
def get_kicks_products(talla="9.5", min_price=0, max_price=99999):
    print("🔄 Obteniendo productos de KICKS...")
    url = "https://www.kicks.com.gt/sale-tienda"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    productos = []
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        items = soup.find_all("li", class_="item product product-item")
        for item in items:
            try:
                nombre_tag = item.find("strong", class_="product name product-item-name")
                link_tag = nombre_tag.find("a")
                nombre = nombre_tag.get_text(strip=True)
                link = link_tag["href"]

                if not link.startswith("http"):
                    url_producto = f"https://www.kicks.com.gt{link}"
                else:
                    url_producto = link

                # Obtener detalle del producto
                detalle_response = requests.get(url_producto, headers=headers, timeout=10)
                detalle_response.raise_for_status()
                detalle_soup = BeautifulSoup(detalle_response.text, "html.parser")

                script_tag = detalle_soup.find("script", text=lambda t: t and "var spConfig" in t)
                if not script_tag:
                    continue

                tallas_text = detalle_soup.get_text().lower()
                if talla.replace(".", "") not in tallas_text.replace(".", ""):
                    continue

                precio_tag = item.find("span", class_="price-wrapper")
                if precio_tag:
                    precio_text = precio_tag.get("data-price-amount")
                    precio = float(precio_text)
                else:
                    continue

                if min_price <= precio <= max_price:
                    imagen_tag = item.find("img")
                    imagen = imagen_tag["src"] if imagen_tag else ""

                    productos.append({
                        "nombre": nombre,
                        "precio": precio,
                        "url": url_producto,
                        "imagen": imagen
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
        "KICKS": get_kicks_products(talla, min_price, max_price)
        # "Bitterheads": get_bitterheads_products(talla, min_price, max_price),  # se puede reactivar cuando esté listo
    }
