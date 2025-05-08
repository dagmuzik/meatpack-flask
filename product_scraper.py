import requests
from bs4 import BeautifulSoup

def get_meatpack_products(talla_busqueda="9.5"):
    URL = "https://meatpack.com/collections/special-price/products.json"
    response = requests.get(URL)
    data = response.json()

    productos = []
    for producto in data.get("products", []):
        nombre = producto["title"]
        handle = producto["handle"]
        url = f"https://meatpack.com/products/{handle}"
        tienda = "Meatpack"
        marca = nombre.split()[0] if nombre else "Desconocida"

        for variante in producto.get("variants", []):
            talla = variante["option1"]
            disponible = variante["available"]
            precio = float(variante["price"])
            if precio > 1000:
                precio = precio / 100

            compare_at = variante["compare_at_price"]
            if compare_at:
                compare_at = float(compare_at)
                if compare_at > 1000:
                    compare_at = compare_at / 100
            else:
                compare_at = None

            if talla_busqueda in talla and disponible:
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
                    "url": url
                })

    return sorted(productos, key=lambda x: x["precio_final"])


def get_lagrieta_products(talla_busqueda="9.5"):
    URL = "https://lagrieta.gt/collections/ultimas-tallas"
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, "html.parser")
    productos = []

    tienda = "La Grieta"

    for producto in soup.select(".productgrid--item"):
        nombre_tag = producto.select_one(".productitem--title")
        url_tag = producto.select_one("a")
        precio_tag = producto.select_one(".price__current")
        tallas_tag = producto.select_one(".productitem--variants")

        if not (nombre_tag and url_tag and precio_tag and tallas_tag):
            continue

        nombre = nombre_tag.get_text(strip=True)
        url = "https://lagrieta.gt" + url_tag["href"]
        marca = nombre.split()[0]
        precio_texto = precio_tag.get_text(strip=True).replace("Q", "").replace(",", "")
        try:
            precio = float(precio_texto)
        except:
            continue

        tallas = [t.strip() for t in tallas_tag.get_text(strip=True).split("/")]
        if talla_busqueda in tallas:
            productos.append({
                "marca": marca,
                "nombre": nombre,
                "precio_final": precio,
                "precio_original": None,
                "descuento": "",
                "talla": talla_busqueda,
                "tienda": tienda,
                "url": url
            })

    return sorted(productos, key=lambda x: x["precio_final"])


def get_all_products(talla="9.5"):
    return {
        "Meatpack": get_meatpack_products(talla),
        "La Grieta": get_lagrieta_products(talla)
    }
