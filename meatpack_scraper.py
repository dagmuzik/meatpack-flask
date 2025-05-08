import requests

def get_products(talla_busqueda="9.5"):
    URL = "https://meatpack.com/collections/special-price/products.json"
    response = requests.get(URL)
    data = response.json()

    productos_filtrados = []

    for producto in data.get("products", []):
        nombre = producto["title"]
        handle = producto["handle"]
        url = f"https://meatpack.com/products/{handle}"
        tienda = "Meatpack"
        marca = nombre.split()[0] if nombre else "Desconocida"

        for variante in producto.get("variants", []):
            talla = variante["option1"]
            disponible = variante["available"]
            
            # Formateo del precio
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

            # Filtrado por talla
            if talla_busqueda in talla and disponible:
                descuento = ""
                if compare_at and compare_at > precio:
                    descuento = f"{round((compare_at - precio) / compare_at * 100)}%"

                productos_filtrados.append({
                    "marca": marca,
                    "nombre": nombre,
                    "precio_final": f"Q{precio:,.2f}",
                    "precio_original": f"Q{compare_at:,.2f}" if compare_at else "",
                    "descuento": descuento,
                    "talla": talla,
                    "tienda": tienda,
                    "url": url
                })

    productos_filtrados.sort(key=lambda x: x["marca"].lower())
    return productos_filtrados
