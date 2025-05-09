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

def get_product_details(url_producto):
    """Scrapea la página del producto individual de KICKS para extraer tallas visibles."""
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url_producto, headers=headers, timeout=10)
        if response.status_code != 200:
            logging.warning(f"⚠️ Producto no disponible: {url_producto}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        tallas = []
        talla_tags = soup.select(".swatch-option.text")

        for tag in talla_tags:
            talla = tag.get("data-option-label") or tag.text.strip()
            if talla:
                tallas.append(talla)

        logging.info(f"🔎 Tallas visibles en {url_producto}: {tallas}")
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

        for item in items[:10]:  # 🔁 limitar a los primeros 10
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
        "KICKS": get_kicks_products(talla, min_price, max_price)
    }
