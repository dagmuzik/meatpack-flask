import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

MAPA_TALLAS = {
    "139": "5.5", "142": "5.75", "145": "6", "148": "6.5", "151": "7", "154": "7.5",
    "157": "8", "160": "8.5", "163": "9", "166": "9.5", "169": "10", "172": "10.5",
    "175": "11", "178": "11.5", "181": "12", "184": "12.5", "187": "13", "190": "13.5",
    "193": "14", "196": "14.5", "199": "15", "752": "15.5?"
}

BASE_KICKS_API = "https://www.kicks.com.gt/rest/V1"
BASE_KICKS_WEB = "https://www.kicks.com.gt"

def get_json(url, headers=None, params=None):
    try:
        headers = headers or {}
        headers.update(HEADERS)
        response = requests.get(url, headers=headers, params=params, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"⚠️ Error solicitando {url}: {e}")
        return {}

def normalizar_talla(t):
    return re.sub(r"[^\d]", "", str(t))

def talla_coincide(talla_buscada, talla_encontrada):
    return normalizar_talla(talla_buscada) == normalizar_talla(talla_encontrada)

def inferir_marca(nombre):
    nombre = nombre.lower()
    if "sl 72" in nombre or "forum" in nombre or "gazelle" in nombre or "stan smith" in nombre:
        return "adidas"
    if "slip-on" in nombre or "sk8-hi" in nombre or "ultrarange" in nombre or "old Skool" in nombre:
        return "vans"
    if "chuck" in nombre:
        return "converse"
    if "nike" in nombre or "air" in nombre or "kobe" in nombre or "jelly ma" in nombre:
        return "nike"
    if "new balance" in nombre:
        return "new balance"
    if "dellow" in nombre:
        return "stepney workers club"
    if "shadow" in nombre or "grid azura" in nombre:
        return "saucony"
    if "nitro" in nombre:
        return "puma"
    return ""

def obtener_shopify(url, tienda, talla):
    try:
        data = get_json(url)
    except Exception as e:
        print(f"❌ Error al obtener datos de {tienda}: {e}")
        return []

    productos = []
    for prod in data.get("products", []):
        img = prod.get("images", [{}])[0].get("src", "https://via.placeholder.com/240x200?text=Sneaker")
        for var in prod.get("variants", []):
            if talla_coincide(talla, var.get("title", "")) and var.get("available"):
                try:
                    precio = float(var["price"])
                    productos.append({
                        "Producto": prod["title"],
                        "Talla": var["title"],
                        "Precio": precio,
                        "Marca": inferir_marca(prod["title"]),
                        "Tienda": tienda,
                        "URL": f'https://{url.split("/")[2]}/products/{prod["handle"]}',
                        "Imagen": img
                    })
                except Exception as e:
                    print(f"⚠️ Error al procesar producto {prod.get('title')}: {e}")
    return productos


def obtener_meatpack(talla):
    return obtener_shopify("https://meatpack.com/collections/special-price/products.json", "Meatpack", talla)

def obtener_lagrieta(talla):
    return obtener_shopify("https://lagrieta.gt/collections/ultimas-tallas/products.json", "La Grieta", talla)

import requests
from bs4 import BeautifulSoup

def obtener_premiumtrendy(talla):
    productos_disponibles = []
    page = 1
    max_pages = 2
    base_url = "https://premiumtrendygt.com"
    products_api = f"{base_url}/wp-json/wc/store/products"
    headers = {"User-Agent": "Mozilla/5.0"}

    etiquetas_invalidas = {"clothing", "accesorios", "birkenstock", "blackclover", "ralph lauren", "true"}

    def detectar_atributo_talla(html):
        try:
            soup = BeautifulSoup(html, "html.parser")
            select = soup.find("select", {"name": lambda x: x and "attribute_pa_talla" in x})
            return select["name"] if select else None
        except Exception as e:
            print(f"⚠️ Error al analizar HTML para atributo de talla: {e}")
            return None

    def producto_valido(prod):
        nombre = prod.get("name")
        url = prod.get("permalink")
        etiquetas = {tag["name"].lower() for tag in prod.get("tags", [])}
        if "sneakers" not in etiquetas or etiquetas & etiquetas_invalidas:
            print(f"⏭️ {nombre} — Ignorado por etiquetas: {etiquetas}")
            return None

        try:
            html = requests.get(url, headers=headers, timeout=6).text
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Error obteniendo HTML de {nombre}: {e}")
            return None

        atributo = detectar_atributo_talla(html)
        if not atributo:
            print(f"⏭️ {nombre} — Sin atributo de talla")
            return None

        url_con_talla = f"{url}?{atributo}={talla}"
        try:
            r = requests.get(url_con_talla, headers=headers, timeout=6)
            if r.status_code != 200:
                print(f"⚠️ {nombre} — respuesta {r.status_code}")
                return None
            soup = BeautifulSoup(r.text, "html.parser")
            boton = soup.select_one("button.single_add_to_cart_button")
            if not boton or "disabled" in boton.get("class", []):
                print(f"❌ {nombre} — Talla {talla} no disponible")
                return None
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Timeout u error al verificar {nombre}: {e}")
            return None

        precios = prod.get("prices", {})
        regular = int(precios.get("regular_price", 0)) / 100
        oferta = int(precios.get("sale_price", 0)) / 100
        precio_final = oferta if oferta > 0 else regular
        if precio_final == 0:
            return None

        return {
            "Producto": nombre,
            "Talla": talla,
            "Precio": precio_final,
            "URL": url,
            "Imagen": prod.get("images", [{}])[0].get("src", ""),
            "Tienda": "Premium Trendy",
            "Marca": inferir_marca(nombre)
        }

    while page <= max_pages:
        print(f"🔄 Premium Trendy página {page}...")
        try:
            resp = requests.get(products_api, headers=headers, params={"on_sale": "true", "per_page": 40, "page": page}, timeout=10)
            if resp.status_code != 200:
                print(f"❌ Error HTTP {resp.status_code} en página {page}")
                break
            productos = resp.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error solicitando productos en página {page}: {e}")
            break

        if not productos:
            print("✅ Fin productos Premium Trendy")
            break

        for prod in productos:
            if len(productos_disponibles) >= 10:
                return productos_disponibles
            resultado = producto_valido(prod)
            if resultado:
                productos_disponibles.append(resultado)

        page += 1

    return productos_disponibles

def obtener_bitterheads(talla):
    productos = []
    vistos = set()
    for page in range(1, 3):
        url = f"https://www.bitterheads.com/api/catalog_system/pub/products/search?fq=productClusterIds:159&ps=24&pg={page}"
        prods = get_json(url)
        for p in prods:
            if p['productId'] in vistos:
                continue
            tallas_disp = get_json(f"https://www.bitterheads.com/api/catalog_system/pub/products/variations/{p['productId']}")
            for sku in tallas_disp.get("skus", []):
                talla_sku = sku["dimensions"].get("Talla", "")
                if talla_coincide(talla, talla_sku) and sku.get("available"):
                    productos.append({
                        "Producto": p["productName"],
                        "Talla": talla_sku,
                        "Precio": p["items"][0]["sellers"][0]["commertialOffer"]["Price"],
                        "Marca": inferir_marca(p["productName"]),
                        "Tienda": "Bitterheads",
                        "URL": f"https://www.bitterheads.com/{p['linkText']}/p",
                        "Imagen": p.get("items", [{}])[0].get("images", [{}])[0].get("imageUrl", "https://via.placeholder.com/240x200?text=Sneaker")
                    })
                    vistos.add(p['productId'])
                    break
    return productos

def obtener_adidas(talla):
    productos = []
    keywords = ["tenis", "sneaker", "zapatilla", "forum", "ultraboost", "nmd", "rivalry", "gazelle", "campus", "samba", "run", "ozweego"]
    for page in range(2):
        url = f"https://www.adidas.com.gt/api/catalog_system/pub/products/search?fq=productClusterIds:138&_from={page*50}&_to={(page+1)*50-1}"
        productos.extend(get_json(url))
    resultados = []
    for producto in productos:
        nombre = producto.get("productName", "").lower()
        if not any(k in nombre for k in keywords):
            continue
        product_id = producto.get("productId")
        variaciones = get_json(f"https://www.adidas.com.gt/api/catalog_system/pub/products/variations/{product_id}")
        for sku in variaciones.get("skus", []):
            talla_sku = sku["dimensions"].get("Talla", "")
            if talla_coincide(talla, talla_sku) and sku.get("available", False):
                resultados.append({
                    "Producto": producto["productName"],
                    "Talla": talla_sku,
                    "Precio": sku["bestPrice"] / 100,
                    "Marca": "adidas",
                    "Tienda": "Adidas",
                    "URL": f"https://www.adidas.com.gt/{producto.get('linkText')}/p",
                    "Imagen": producto.get("items", [{}])[0].get("images", [{}])[0].get("imageUrl", "https://via.placeholder.com/240x200?text=Sneaker")
                })
    return resultados

def obtener_kicks(talla_buscada):
    skus = {}
    for pagina in range(1, 3):
        url = f"https://www.kicks.com.gt/marcas.html?p={pagina}&product_list_limit=36&special_price=29.99-1749.99&tipo_1=241"
        try:
            res = requests.get(url, headers=HEADERS, timeout=5)
            soup = BeautifulSoup(res.text, "html.parser")
            links = soup.select(".product-item-info a")
            hrefs = {a.get("href") for a in links if a.get("href", "").endswith(".html")}
            for href in hrefs:
                match = re.search(r"(\d{8})", href)
                if match:
                    skus[match.group(1)] = href
        except Exception as e:
            print(f"Error parsing página {pagina}: {e}")
            continue

    resultados = []
    for i, (sku_padre, href) in enumerate(skus.items()):
        if i >= 10:
            break
        padre_url = f"{BASE_KICKS_API}/products/{sku_padre}?storeCode=kicks_gt"
        data = get_json(padre_url)
        if not data or data.get("type_id") != "configurable":
            continue
        atributos = {attr["attribute_code"]: attr.get("value") for attr in data.get("custom_attributes", [])}
        nombre = data.get("name")
        url_key = atributos.get("url_key")
        url_producto = f"{BASE_KICKS_WEB}/{url_key}.html" if url_key else href

        imagen = None
        for attri in data.get("custom_attributes", []):
            if attri.get("attribute_code") == "image":
                imagen = f"https://www.kicks.com.gt/media/catalog/product{attri.get('value')}"
                break
        if not imagen:
            imagen = "https://via.placeholder.com/240x200?text=Sneaker"

        variantes_url = f"{BASE_KICKS_API}/configurable-products/{sku_padre}/children?storeCode=kicks_gt"
        variantes = get_json(variantes_url)
        for var in variantes:
            attr = {a["attribute_code"]: a.get("value") for a in var.get("custom_attributes", [])}
            talla_id = attr.get("talla_calzado")
            talla_texto = MAPA_TALLAS.get(talla_id, talla_id)
            if not talla_coincide(talla_buscada, talla_texto):
                continue
            special_price = attr.get("special_price")
            if not special_price:
                continue
            precio = float(special_price)
            resultados.append({
                "Producto": nombre,
                "Talla": talla_texto,
                "Precio": precio,
                "Marca": inferir_marca(nombre),
                "Tienda": "Kicks",
                "URL": url_producto,
                "Imagen": imagen
            })
    return resultados

def buscar_todos(talla="", tienda="", marca=""):
    from pandas import DataFrame

    print(f"\n🔎 Buscando productos talla {talla or '[cualquiera]'} en tienda: {tienda or 'Todas'} con marca: {marca or 'Todas'}")

    resultados = []

    if tienda in ("", "Adidas"):
        try:
            resultados += obtener_adidas(talla)
        except Exception as e:
            print(f"❌ Error en Adidas: {e}")

    if tienda in ("", "Kicks"):
        try:
            resultados += obtener_kicks(talla)
        except Exception as e:
            print(f"❌ Error en Kicks: {e}")

    if tienda in ("", "Bitterheads"):
        try:
            resultados += obtener_bitterheads(talla)
        except Exception as e:
            print(f"❌ Error en Bitterheads: {e}")

    if tienda in ("", "Meatpack"):
        try:
            resultados += obtener_meatpack(talla)
        except Exception as e:
            print(f"❌ Error en Meatpack: {e}")

    if tienda in ("", "La Grieta"):
        try:
            resultados += obtener_lagrieta(talla)
        except Exception as e:
            print(f"❌ Error en La Grieta: {e}")

    if tienda in ("", "Premium Trendy"):
        try:
            resultados += obtener_premiumtrendy(talla)
        except Exception as e:
            print(f"❌ Error en Premium Trendy: {e}")

    # Filtrar por marca si se indicó
    if marca:
        marca = marca.strip().lower()
        resultados = [p for p in resultados if p.get("Marca", "").lower() == marca]

    try:
        return DataFrame(resultados).sort_values(by="Precio").to_dict("records")
    except Exception as e:
        print("❌ Error final al ordenar/convertir:", str(e))
        return []


