import requests

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

            precio_raw = float(variante["price"])
            precio = precio_raw / 100 if precio_raw % 100 == 0 else precio_raw

            compare_at_raw = variante.get("compare_at_price")
            if compare_at_raw:
                compare_at_raw = float(compare_at_raw)
                compare_at = compare_at_raw / 100 if compare_at_raw % 100 == 0 else compare_at_raw
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
    URL = "https://lagrieta.gt/collections/ultimas-tallas/products.json"
    response = requests.get(URL)
    data = response.json()

    productos = []
    tienda = "La Grieta"

    for producto in data["products"]:
        nombre = producto["title"]
        handle = producto["handle"]
        url = f"https://lagrieta.gt/products/{handle}"
        marca = nombre.split()[0] if nombre else "Desconocida"

        for variante in producto["variants"]:
            talla = variante["title"]
            disponible = variante["available"]
            if talla_busqueda in talla and disponible:
                try:
                    precio = float(variante["price"])
                except:
                    precio = None

                productos.append({
                    "marca": marca,
                    "nombre": nombre,
                    "precio_final": precio,
                    "precio_original": None,
                    "descuento": "",
                    "talla": talla,
                    "tienda": tienda,
                    "url": url
                })

    return sorted(productos, key=lambda x: x["precio_final"])


def get_all_products(talla="9.5"):
    return {
        "Meatpack": get_meatpack_products(talla),
        "La Grieta": get_lagrieta_products(talla)
    }
