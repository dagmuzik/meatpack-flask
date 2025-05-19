# scraping_tiendas.py

from utils import get_json, talla_coincide, inferir_marca, inferir_genero, MAPA_TALLAS, headers
import requests
import time
import re
from bs4 import BeautifulSoup

def obtener_shopify(url, tienda, talla):
    productos = []
    data = get_json(url)
    for prod in data.get("products", []):
        img = prod.get("images", [{}])[0].get("src", "https://via.placeholder.com/240x200?text=Sneaker")
        for var in prod.get("variants", []):
            if (not talla or talla_coincide(talla, var.get("title", ""))) and var.get("available"):
                try:
                    precio = float(var["price"])
                    nombre = prod["title"]
                    genero = inferir_genero(nombre)
                    productos.append({
                        "Producto": nombre,
                        "Talla": var["title"],
                        "Precio": precio,
                        "Marca": inferir_marca(nombre),
                        "Genero": genero,
                        "Tienda": tienda,
                        "URL": f'https://{url.split("/")[2]}/products/{prod["handle"]}',
                        "Imagen": img
                    })
                except Exception as e:
                    print(f"⚠️ Error al procesar producto {prod.get('title')}: {e}")
    return productos

def obtener_meatpack(talla):
    return obtener_shopify("https://meatpack.com/collections/special-price/products.json", "meatpack", talla)

def obtener_lagrieta(talla):
    return obtener_shopify("https://lagrieta.gt/collections/ultimas-tallas/products.json", "lagrieta", talla)

def obtener_adidas_estandarizado():
    productos = []
    page = 0
    paso = 50
    MAX_PAGES = 6
    base_url = "https://www.adidas.com.gt/api/catalog_system/pub/products/search?fq=productClusterIds:138&_from={inicio}&_to={fin}"

    def get_variaciones(product_id):
        url = f"https://www.adidas.com.gt/api/catalog_system/pub/products/variations/{product_id}"
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"❌ Error obteniendo variaciones de {product_id}: {e}")
            return {}

    while page < MAX_PAGES:
        url = base_url.format(inicio=page * paso, fin=(page + 1) * paso - 1)
        data = get_json(url)
        if not data:
            break

        for producto in data:
            product_id = producto.get("productId")
            variaciones = get_variaciones(product_id)
            for item in producto.get("items", []):
                for seller in item.get("sellers", []):
                    offer = seller.get("commertialOffer", {})
                    if offer.get("IsAvailable") and offer.get("Price", 0) > 0:
                        productos.append({
                            "sku": item.get("itemId"),
                            "nombre": producto.get("productName"),
                            "precio": offer["Price"],
                            "talla": item.get("name"),
                            "imagen": item.get("images", [{}])[0].get("imageUrl", ""),
                            "link": f"https://www.adidas.com.gt/{producto.get('linkText')}/p",
                            "tienda": "adidas",
                            "marca": producto.get("brand", "").lower(),
                            "genero": variaciones.get("Talle", {}).get(item.get("itemId"), "").lower()
                        })
        page += 1

    print(f"✅ Adidas: {len(productos)} productos válidos.")
    return productos

def obtener_kicks(talla_buscada=""):
    BASE_API = "https://www.kicks.com.gt/rest/V1"
    BASE_WEB = "https://www.kicks.com.gt"
    MAPA_GENERO = {"286": "hombre", "289": "mujer", "644": "niños"}

    skus = {}
    for pagina in range(1, 3):
        try:
            url = f"{BASE_WEB}/marcas.html?p={pagina}&product_list_limit=36&special_price=29.99-1749.99&tipo_1=241"
            res = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            links = soup.select(".product-item-info a")
            hrefs = {a.get("href") for a in links if a.get("href", "").endswith(".html")}
            for href in hrefs:
                match = re.search(r"(\d{8})", href)
                if match:
                    skus[match.group(1)] = href
        except Exception as e:
            print(f"⚠️ Error leyendo página {pagina}: {e}")

    resultados = []
    for sku_padre, href in skus.items():
        padre_url = f"{BASE_API}/products/{sku_padre}?storeCode=kicks_gt"
        data = get_json(padre_url)
        if not data or data.get("type_id") != "configurable":
            continue

        atributos = {attr["attribute_code"]: attr.get("value") for attr in data.get("custom_attributes", [])}
        nombre = data.get("name", "")
        url_key = atributos.get("url_key")
        url_producto = f"{BASE_WEB}/{url_key}.html" if url_key else href

        imagen = next(
            (f"{BASE_WEB}/media/catalog/product{a.get('value')}"
             for a in data.get("custom_attributes", [])
             if a.get("attribute_code") == "image"),
            "https://via.placeholder.com/240x200?text=Sneaker"
        )

        genero = MAPA_GENERO.get(atributos.get("genero"), "")

        variantes_url = f"{BASE_API}/configurable-products/{sku_padre}/children?storeCode=kicks_gt"
        variantes = get_json(variantes_url)
        for var in variantes:
            attr = {a["attribute_code"]: a.get("value") for a in var.get("custom_attributes", [])}
            talla_id = attr.get("talla_calzado")
            talla_texto = MAPA_TALLAS.get(talla_id, talla_id)
            if talla_buscada and talla_buscada != talla_texto:
                continue
            special_price = attr.get("special_price")
            if not special_price:
                continue
            try:
                precio = float(special_price)
            except:
                continue
            resultados.append({
                "sku": var.get("sku"),
                "nombre": nombre,
                "precio": precio,
                "talla": talla_texto,
                "imagen": imagen,
                "link": url_producto,
                "tienda": "kicks",
                "marca": inferir_marca(nombre),
                "genero": genero
            })

    print(f"✅ Kicks: {len(resultados)} productos válidos.")
    return resultados

def obtener_bitterheads():
    BASE_URL = "https://www.bitterheads.com"
    PAGE_SIZE = 24
    MAX_PAGES = 80
    productos_data = []
    productos_vistos = set()

    def get_available_tallas(product_id):
        url = f"{BASE_URL}/api/catalog_system/pub/products/variations/{product_id}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            return []
        data = response.json()
        return [sku.get("dimensions", {}).get("Talla", "")
                for sku in data.get("skus", []) if sku.get("available") and sku.get("availablequantity", 0) > 0]

    for page in range(1, MAX_PAGES + 1):
        url = f"{BASE_URL}/api/catalog_system/pub/products/search?fq=productClusterIds:159&ps={PAGE_SIZE}&pg={page}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code not in [200, 206]:
            break
        productos = response.json()
        if not productos:
            break

        for p in productos:
            link_text = p.get("linkText")
            product_id = p.get("productId")
            if not link_text or not product_id or link_text in productos_vistos:
                continue
            productos_vistos.add(link_text)

            nombre = p.get("productName", "")
            marca = p.get("brand", "")
            link = f"{BASE_URL}/{link_text}/p"

            precio = None
            imagen = ""
            if p.get("items"):
                item = p["items"][0]
                if item.get("sellers"):
                    oferta = item["sellers"][0]["commertialOffer"]
                    precio = oferta.get("Price")
                if item.get("images"):
                    imagen = item["images"][0].get("imageUrl", "")

            if precio and precio > 0:
                tallas_disponibles = get_available_tallas(product_id)
                if not tallas_disponibles:
                    continue
                productos_data.append({
                    "sku": "",
                    "nombre": nombre,
                    "precio": float(precio),
                    "talla": ", ".join(tallas_disponibles),
                    "imagen": imagen,
                    "link": link,
                    "tienda": "bitterheads",
                    "marca": marca.lower(),
                    "genero": ""
                })
        time.sleep(0.5)

    print(f"✅ Bitterheads: {len(productos_data)} productos disponibles.")
    return productos_data

def obtener_premiumtrendy():
    BASE_URL = "https://premiumtrendygt.com"
    API_URL = f"{BASE_URL}/wp-json/wc/store/products"
    productos_disponibles = []
    page = 1

    while True:
        print(f"📦 Premium Trendy - Página {page}")
        try:
            r = requests.get(API_URL, headers=HEADERS, params={"on_sale": "true", "per_page": 100, "page": page}, timeout=10)
            if r.status_code != 200:
                break
            productos = r.json()
            if not productos:
                break
        except Exception as e:
            print(f"❌ Error en Premium Trendy página {page}: {e}")
            break

        for prod in productos:
            try:
                nombre = prod.get("name", "")
                url = prod.get("permalink", "")
                sku = prod.get("sku", "")
                imagen = prod.get("images", [{}])[0].get("src", "")
                etiquetas = [tag.get("name", "").lower() for tag in prod.get("tags", [])]

                if "sneakers" not in etiquetas or any(e in etiquetas for e in ["clothing", "true"]):
                    continue

                precios = prod.get("prices", {})
                regular = int(precios.get("regular_price", 0)) / 100
                oferta = int(precios.get("sale_price", 0)) / 100
                precio = oferta if oferta > 0 else regular
                if precio == 0:
                    continue

                marca = ""
                for attr in prod.get("attributes", []):
                    if attr.get("name", "").lower() == "marca":
                        terms = attr.get("terms", [])
                        if terms:
                            marca = terms[0].get("name", "").strip().lower()
                            break

                tallas_disponibles = set()
                for var in prod.get("variations", []):
                    for a in var.get("attributes", []):
                        if "talla" in a.get("name", "").lower():
                            valor = a.get("value", "").strip()
                            if valor:
                                tallas_disponibles.add(valor)

                for talla in tallas_disponibles:
                    productos_disponibles.append({
                        "sku": sku,
                        "nombre": nombre,
                        "precio": precio,
                        "talla": talla,
                        "imagen": imagen,
                        "link": url,
                        "tienda": "premiumtrendy",
                        "marca": marca,
                        "genero": ""
                    })

            except Exception as e:
                print(f"⚠️ Error procesando producto Premium Trendy: {e}")
                continue

        page += 1
        time.sleep(0.5)

    print(f"✅ Premium Trendy: {len(productos_disponibles)} productos disponibles.")
    return productos_disponibles

def obtener_veinteavenida():
    productos = []
    base_url = "https://veinteavenida.com/product-category/sale/page/"
  
    for page in range(1, 4):
        print(f"📦 Veinte Avenida - Página {page}")
        url = f"{base_url}{page}/"
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code != 200:
                break
            soup = BeautifulSoup(res.text, "html.parser")
            items = soup.select("li.product")
            if not items:
                break
        except Exception as e:
            print(f"❌ Error cargando página {page}: {e}")
            break

        for item in items:
            try:
                nombre_tag = item.select_one("a.product-loop-title h3.woocommerce-loop-product__title")
                url_tag = item.select_one("a.product-loop-title")
                img_tag = item.select_one("img.wp-post-image")

                if not (nombre_tag and url_tag and img_tag):
                    continue

                nombre = nombre_tag.text.strip()
                url_producto = url_tag["href"]
                imagen = img_tag["src"]

                detalle = requests.get(url_producto, headers=HEADERS, timeout=10)
                soup_detalle = BeautifulSoup(detalle.text, "html.parser")

                precios = soup_detalle.select("p.price span.woocommerce-Price-amount")
                if len(precios) >= 2:
                    precio_final = precios[1].text.strip().replace("Q", "").replace(",", "")
                elif len(precios) == 1:
                    precio_final = precios[0].text.strip().replace("Q", "").replace(",", "")
                else:
                    continue

                try:
                    precio = float(precio_final)
                    if precio <= 0:
                        continue
                except:
                    continue

                tallas = []
                for div in soup_detalle.select(".tfwctool-varation-swatch-preview"):
                    talla_html = div.get("data-bs-original-title") or div.text.strip()
                    if talla_html:
                        tallas.append(talla_html)

                productos.append({
                    "sku": "",
                    "nombre": nombre,
                    "precio": precio,
                    "talla": ", ".join(tallas),
                    "imagen": imagen,
                    "link": url_producto,
                    "tienda": "veinte avenida",
                    "marca": inferir_marca(nombre),
                    "genero": inferir_genero(nombre)
                })

            except Exception as e:
                print(f"⚠️ Error procesando producto: {e}")
                continue

        time.sleep(0.5)

    print(f"✅ Veinte Avenida: {len(productos)} productos disponibles.")
    return productos

def obtener_deportesdelcentro():
    base_url = "https://deporteselcentro.com/wp-json/wc/store/v1/products"
    
    productos_disponibles = []
    pagina = 1
    max_pages = 10

    while pagina <= max_pages:
        try:
            response = requests.get(base_url, params={"page": pagina, "per_page": 100}, headers=HEADERS, timeout=10)
            if response.status_code != 200:
                print(f"❌ Error HTTP {response.status_code} en página {pagina}")
                break
            productos = response.json()
        except Exception as e:
            print(f"❌ Error conectando: {e}")
            break

        if not productos:
            break

        for producto in productos:
            try:
                precios = producto.get("prices", {})
                regular = int(precios.get("regular_price", 0))
                oferta = int(precios.get("sale_price", 0))
                on_sale = producto.get("on_sale", False)

                if not on_sale or oferta <= 0 or oferta >= regular:
                    continue

                tallas = []
                for atributo in producto.get("attributes", []):
                    if atributo.get("name", "").lower() == "talla":
                        tallas = [term.get("name") for term in atributo.get("terms", [])]

                for talla in tallas:
                    productos_disponibles.append({
                        "sku": producto.get("sku", ""),
                        "nombre": producto.get("name", ""),
                        "precio": oferta / 100,
                        "talla": talla,
                        "imagen": producto.get("images", [{}])[0].get("src", ""),
                        "link": producto.get("permalink", ""),
                        "tienda": "deportesdelcentro",
                        "marca": producto.get("brands", [{}])[0].get("name", "") if producto.get("brands") else "",
                        "genero": ""
                    })
            except Exception as e:
                print(f"⚠️ Error procesando producto: {e}")
                continue

        pagina += 1

    print(f"✅ Deportes del Centro: {len(productos_disponibles)} productos en promoción.")
    return productos_disponibles

