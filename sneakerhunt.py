import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

HEADERS = {"User-Agent": "Mozilla/5.0"}

# Función genérica para realizar solicitudes HTTP
def get_json(url, headers=None, params=None):
    response = requests.get(url, headers=headers or HEADERS, params=params)
    return response.json() if response.ok else {}

# Adidas

def obtener_adidas(talla):
    productos = []
    for page in range(10):
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
                    "URL": f"https://www.adidas.com.gt/{producto.get('linkText')}/p"
                })
    return resultados

# Meatpack y La Grieta

def obtener_shopify(url, tienda, talla):
    data = get_json(url)
    productos = []
    for prod in data.get("products", []):
        for var in prod["variants"]:
            if talla in var["title"] and var["available"]:
                precio = float(var["price"]) / 100 if tienda == "Meatpack" else float(var["price"])
                productos.append({
                    "Tienda": tienda,
                    "Producto": prod["title"],
                    "Talla": var["title"],
                    "Precio": precio,
                    "URL": f'{url.split(".com")[0]}.com/products/{prod["handle"]}'
                })
    return productos

# Bitterheads

def obtener_bitterheads(talla):
    productos = []
    for page in range(1, 81):
        url = f"https://www.bitterheads.com/api/catalog_system/pub/products/search?fq=productClusterIds:159&ps=24&pg={page}"
        prods = get_json(url)
        for p in prods:
            tallas_disp = get_json(f"https://www.bitterheads.com/api/catalog_system/pub/products/variations/{p['productId']}")
            tallas = [sku["dimensions"]["Talla"] for sku in tallas_disp.get("skus", []) if sku["available"]]
            if talla in tallas:
                productos.append({
                    "Producto": p["productName"],
                    "Precio": p["items"][0]["sellers"][0]["commertialOffer"]["Price"],
                    "URL": f"https://www.bitterheads.com/{p['linkText']}/p",
                    "Tallas": ", ".join(tallas)
                })
    return productos

# Deportes del Centro

def obtener_deportesdelcentro(talla):
    productos = []
    for page in range(1, 11):
        data = get_json("https://deporteselcentro.com/wp-json/wc/store/v1/products", params={"page": page, "per_page": 100})
        for prod in data:
            tallas = [term["name"] for attr in prod["attributes"] if attr["name"].lower() == "talla" for term in attr["terms"]]
            if talla in tallas and prod["on_sale"]:
                productos.append({
                    "Producto": prod["name"],
                    "Precio": int(prod["prices"]["sale_price"]) / 100,
                    "URL": prod["permalink"],
                    "Tallas": ", ".join(tallas)
                })
    return productos

# Premium Trendy

def obtener_premiumtrendy():
    productos = []
    page = 1
    while True:
        data = get_json("https://premiumtrendygt.com/wp-json/wc/store/products", params={"on_sale": "true", "page": page, "per_page": 100})
        if not data: break
        productos += [{"Producto": p["name"], "Precio": int(p["prices"]["sale_price"])/100, "URL": p["permalink"]} for p in data]
        page += 1
    return productos

# Función principal

def buscar_todos(talla="9.5"):
    resultados = []
    resultados += obtener_adidas(talla)
    resultados += obtener_shopify("https://meatpack.com/collections/special-price/products.json", "Meatpack", talla)
    resultados += obtener_shopify("https://lagrieta.gt/collections/ultimas-tallas/products.json", "La Grieta", talla)
    resultados += obtener_bitterheads(talla)
    resultados += obtener_deportesdelcentro(talla)
    resultados += obtener_premiumtrendy()

    return pd.DataFrame(resultados).sort_values(by="Precio")

if __name__ == "__main__":
    df = buscar_todos("9.5")
    fecha = datetime.now().strftime("%Y-%m-%d")
    df.to_csv(f"ofertas_sneaker_{fecha}.csv", index=False)
    print(df)
