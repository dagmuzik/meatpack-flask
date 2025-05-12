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
    data = get_json(url)
    productos = []
    for prod in data.get("products", []):
        img = prod.get("images", [{}])[0].get("src", "https://via.placeholder.com/240x200?text=Sneaker")
        for var in prod.get("variants", []):
            if talla_coincide(talla, var.get("title", "")) and var.get("available"):
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
    return productos

def obtener_premiumtrendy(talla):
    print(f"🔍 Buscando en Premium Trendy talla {talla}...")
    productos = []
    page = 1

    while True:
        print(f"📄 Página {page}")
        data = get_json(
            "https://premiumtrendygt.com/wp-json/wc/store/products",
            params={"on_sale": "true", "per_page": 100, "page": page}
        )

        if not data:
            print("✅ Fin de productos en Premium Trendy.")
            break

        for item in data:
            nombre = item.get("name")
            precios = item.get("prices", {})
            oferta_raw = precios.get("sale_price")
            if not oferta_raw or float(oferta_raw) <= 0:
                print(f"❌ {nombre} descartado por precio inválido")
                continue

            tallas_raw = []
            disponible = False
            for attr in item.get("attributes", []):
                if "talla" in attr.get("name", "").lower():
                    for term in attr.get("terms", []):
                        talla_term = term.get("name", "").strip()
                        count = term.get("count", 0)
                        tallas_raw.append(f"{talla_term} ({count})")

                        # Mostrar log de tallas
                        print(f"🧪 {nombre} → {talla_term} (stock: {count})")

                        if talla_coincide(talla, talla_term) and count > 0:
                            disponible = True
                            break
                if disponible:
                    break

            if not disponible:
                print(f"⚠️ {nombre} descartado, talla {talla} no disponible.")
                continue

            oferta = float(oferta_raw)
            if oferta > 1000:
                oferta = oferta / 100

            productos.append({
                "Producto": nombre,
                "Talla": talla,
                "Precio": oferta,
                "Marca": inferir_marca(nombre),
                "Tienda": "Premium Trendy",
                "URL": item.get("permalink"),
                "Imagen": item.get("images", [{}])[0].get("src", "https://via.placeholder.com/240x200?text=Sneaker")
            })
            print(f"✅ Agregado: {nombre} - Q{oferta:.2f}")

        page += 1

    print(f"🎯 Total encontrados en Premium Trendy: {len(productos)}")
    return productos

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


