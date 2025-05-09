import requests
from bs4 import BeautifulSoup
import datetime

def get_kicks_products(talla_filtro="9", min_price=0, max_price=99999):
    url_base = "https://www.kicks.com.gt/collections/sale"
    productos_filtrados = []

    page = 1
    while True:
        url = f"{url_base}?page={page}"
        response = requests.get(url)
        if response.status_code != 200:
            break

        soup = BeautifulSoup(response.content, "html.parser")
        productos = soup.select("li.grid__item")

        if not productos:
            break

        for producto in productos:
            nombre_elem = producto.select_one(".card__heading a")
            precio_elem = producto.select_one(".price__sale span, .price__regular span")
            url_producto = nombre_elem["href"] if nombre_elem else None
            nombre = nombre_elem.text.strip() if nombre_elem else "Sin nombre"
            precio = float(precio_elem.text.strip().replace("Q", "").replace(",", "")) if precio_elem else 0

            if not (min_price <= precio <= max_price):
                continue

            if not url_producto.startswith("http"):
                url_producto = "https://www.kicks.com.gt" + url_producto

            producto_detalle = requests.get(url_producto)
            detalle_soup = BeautifulSoup(producto_detalle.content, "html.parser")
            tallas = detalle_soup.select("div[data-option-label]")

            disponible = False
            for talla_div in tallas:
                talla = talla_div.get("data-option-label", "").strip()
                aria_checked = talla_div.get("aria-checked", "")
                if talla == talla_filtro and aria_checked != "false":
                    disponible = True
                    break

            if disponible:
                imagen_elem = producto.select_one("img.motion-reduce")
                imagen_url = "https:" + imagen_elem["src"] if imagen_elem else None
                productos_filtrados.append({
                    "nombre": nombre,
                    "precio": f"Q{precio:.2f}",
                    "url": url_producto,
                    "imagen": imagen_url,
                    "tienda": "Kicks",
                    "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

        page += 1

    return productos_filtrados
