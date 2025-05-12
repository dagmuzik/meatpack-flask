import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
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
    if "sl 72" in nombre:
        return "adidas"
    if "slip on" in nombre or "sk8-hi" in nombre:
        return "vans"
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
                    "URL": f'https://{url.split("/")[2]}/products/{prod["handle"]}',
                    "Imagen": img
                })
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
                    "URL": f"https://www.adidas.com.gt/{producto.get('linkText')}/p",
                    "Imagen": producto.get("items", [{}])[0].get("images", [{}])[0].get("imageUrl", "https://via.placeholder.com/240x200?text=Sneaker")
                })
    return resultados

def obtener_premiumtrendy(talla):
    productos = []
    keywords = ["tenis", "sneaker", "zapatilla", "forum", "ultraboost", "nmd", "rivalry", "gazelle", "campus", "samba"]
    page = 1
    while page <= 2:
        data = get_json("https://premiumtrendygt.com/wp-json/wc/store/products", params={"on_sale": "true", "page": page, "per_page": 100})
        if not data:
            break
        for p in data:
            nombre = p["name"].lower()
            if any(k in nombre for k in keywords):
                tallas = [t["name"] for t in p.get("attributes", []) if t.get("name", "").lower() == "talla"]
                if any(talla_coincide(talla, t) for t in tallas):
                    productos.append({
                        "Producto": p["name"],
                        "Talla": talla,
                        "Precio": float(p["prices"]["sale_price"]) / 100,
                        "Marca": inferir_marca(p["name"]),
                        "URL": p["permalink"],
                        "Imagen": p.get("images", [{}])[0].get("src") if p.get("images") else "https://via.placeholder.com/240x200?text=Sneaker"
                    })
        page += 1
    return productos

def obtener_bitterheads(talla):
    productos = []
    for page in range(1, 3):
        url = f"https://www.bitterheads.com/api/catalog_system/pub/products/search?fq=productClusterIds:159&ps=24&pg={page}"
        prods = get_json(url)
        for p in prods:
            tallas_disp = get_json(f"https://www.bitterheads.com/api/catalog_system/pub/products/variations/{p['productId']}")
            for sku in tallas_disp.get("skus", []):
                talla_sku = sku["dimensions"].get("Talla", "")
                if talla_coincide(talla, talla_sku) and sku.get("available"):
                    productos.append({
                        "Producto": p["productName"],
                        "Talla": talla_sku,
                        "Precio": p["items"][0]["sellers"][0]["commertialOffer"]["Price"] * 100,
                        "Marca": inferir_marca(p["productName"]),
                        "URL": f"https://www.bitterheads.com/{p['linkText']}/p",
                        "Imagen": p.get("items", [{}])[0].get("images", [{}])[0].get("imageUrl", "https://via.placeholder.com/240x200?text=Sneaker")
                    })
    return productos

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
            imagen = f"https://www.kicks.com.gt/media/catalog/product/cache/6/image/400x/040ec09b1e35df139433887a97daa66f/{sku_padre[-3:]}/{sku_padre[-6:-3]}/{sku_padre}.jpg"
            resultados.append({
                "Producto": nombre,
                "Talla": talla_texto,
                "Precio": precio,
                "Marca": inferir_marca(nombre),
                "URL": url_producto,
                "Imagen": imagen
            })
    return resultados

def buscar_todos(talla="9.5"):
    resultados = []
    try:
        resultados += obtener_adidas(talla)
    except Exception as e:
        print(f"❌ Error en Adidas: {e}")
    try:
        resultados += obtener_kicks(talla)
    except Exception as e:
        print(f"❌ Error en Kicks: {e}")
    try:
        resultados += obtener_premiumtrendy(talla)
    except Exception as e:
        print(f"❌ Error en Premium Trendy: {e}")
    try:
        resultados += obtener_bitterheads(talla)
    except Exception as e:
        print(f"❌ Error en Bitterheads: {e}")
    try:
        resultados += obtener_shopify("https://meatpack.com/collections/special-price/products.json", "Meatpack", talla)
        resultados += obtener_shopify("https://lagrieta.gt/collections/ultimas-tallas/products.json", "La Grieta", talla)
    except Exception as e:
        print(f"❌ Error en Shopify: {e}")
    return pd.DataFrame(resultados).sort_values(by="Precio")

