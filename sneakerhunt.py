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

def obtener_adidas(talla):
    productos = []
    for page in range(2):
        url = f"https://www.adidas.com.gt/api/catalog_system/pub/products/search?fq=productClusterIds:138&_from={page*50}&_to={(page+1)*50-1}"
        productos.extend(get_json(url))
    resultados = []
    for producto in productos:
        product_id = producto.get("productId")
        variaciones = get_json(f"https://www.adidas.com.gt/api/catalog_system/pub/products/variations/{product_id}")
        for sku in variaciones.get("skus", []):
            if talla in sku["dimensions"].get("Talla", ""):
                resultados.append({
                    "Producto": producto["productName"],
                    "Talla": sku["dimensions"]["Talla"],
                    "Precio": sku["bestPrice"] / 100,
                    "URL": f"https://www.adidas.com.gt/{producto.get('linkText')}/p",
                    "Imagen": producto.get("items", [{}])[0].get("images", [{}])[0].get("imageUrl", "https://via.placeholder.com/240x200?text=Sneaker")
                })
    return resultados

def obtener_shopify(url, tienda, talla):
    data = get_json(url)
    productos = []
    for prod in data.get("products", []):
        img = prod.get("images", [{}])[0].get("src", "https://via.placeholder.com/240x200?text=Sneaker")
        for var in prod.get("variants", []):
            if talla in var.get("title", "") and var.get("available"):
                precio = float(var["price"]) / 100 if tienda == "Meatpack" else float(var["price"])
                productos.append({
                    "Producto": prod["title"],
                    "Talla": var["title"],
                    "Precio": precio,
                    "URL": f'https://{url.split("/")[2]}/products/{prod["handle"]}',
                    "Imagen": img
                })
    return productos

def obtener_bitterheads(talla):
    productos = []
    for page in range(1, 4):
        url = f"https://www.bitterheads.com/api/catalog_system/pub/products/search?fq=productClusterIds:159&ps=24&pg={page}"
        prods = get_json(url)
        for p in prods:
            tallas_disp = get_json(f"https://www.bitterheads.com/api/catalog_system/pub/products/variations/{p['productId']}")
            tallas = [sku["dimensions"]["Talla"] for sku in tallas_disp.get("skus", []) if sku.get("available")]
            if talla in tallas:
                productos.append({
                    "Producto": p["productName"],
                    "Talla": talla,
                    "Precio": p["items"][0]["sellers"][0]["commertialOffer"]["Price"],
                    "URL": f"https://www.bitterheads.com/{p['linkText']}/p",
                    "Imagen": p.get("items", [{}])[0].get("images", [{}])[0].get("imageUrl", "https://via.placeholder.com/240x200?text=Sneaker")
                })
    return productos

def obtener_deportesdelcentro(talla):
    productos = []
    base_url = "https://deporteselcentro.com/wp-json/wc/store/v1/products"
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "es-ES,es;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    for page in range(1, 6):
        try:
            res = requests.get(base_url, headers=headers, params={"page": page, "per_page": 100}, timeout=5)
            res.raise_for_status()
            productos_data = res.json()
        except Exception as e:
            print(f"❌ Error página {page} - Deportes del Centro: {e}")
            break
        if not productos_data:
            break
        for prod in productos_data:
            tallas = []
            for atributo in prod.get("attributes", []):
                if atributo.get("name", "").lower() == "talla":
                    tallas = [term.get("name") for term in atributo.get("terms", [])]
            sale_price = int(prod["prices"]["sale_price"])
            regular_price = int(prod["prices"]["regular_price"])
            on_sale = prod.get("on_sale", False)
            if talla in tallas and on_sale and sale_price < regular_price:
                productos.append({
                    "Producto": prod["name"],
                    "Talla": talla,
                    "Precio": sale_price / 100,
                    "URL": prod["permalink"],
                    "Imagen": prod.get("images", [{}])[0].get("src", "https://via.placeholder.com/240x200?text=Sneaker")
                })
    return productos

def obtener_premiumtrendy():
    productos = []
    page = 1
    while True:
        data = get_json("https://premiumtrendygt.com/wp-json/wc/store/products", params={"on_sale": "true", "page": page, "per_page": 100})
        if not data:
            break
        for p in data:
            productos.append({
                "Producto": p["name"],
                "Talla": "Única",
                "Precio": int(p["prices"]["sale_price"]) / 100,
                "URL": p["permalink"],
                "Imagen": p.get("images", [{}])[0].get("src") if p.get("images") else "https://via.placeholder.com/240x200?text=Sneaker"
            })
        page += 1
    return productos

def obtener_kicks(talla_buscada):
    skus = {}
    for pagina in range(1, 4):
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
    for sku_padre, href in skus.items():
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
            if talla_texto != talla_buscada:
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
        resultados += obtener_deportesdelcentro(talla)
    except Exception as e:
        print(f"❌ Error en Deportes del Centro: {e}")
    try:
        resultados += obtener_shopify("https://meatpack.com/collections/special-price/products.json", "Meatpack", talla)
        resultados += obtener_shopify("https://lagrieta.gt/collections/ultimas-tallas/products.json", "La Grieta", talla)
    except Exception as e:
        print(f"❌ Error en Shopify: {e}")
    try:
        resultados += obtener_bitterheads(talla)
    except Exception as e:
        print(f"❌ Error en Bitterheads: {e}")
    try:
        resultados += obtener_premiumtrendy()
    except Exception as e:
        print(f"❌ Error en Premium Trendy: {e}")
    return pd.DataFrame(resultados).sort_values(by="Precio")

if __name__ == "__main__":
    df = buscar_todos("9.5")
    fecha = datetime.now().strftime("%Y-%m-%d")
    df.to_csv(f"ofertas_sneaker_{fecha}.csv", index=False)
    print(df)
