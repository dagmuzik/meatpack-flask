import requests
import pandas as pd
from datetime import datetime

HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_json(url, headers=None, params=None):
    try:
        response = requests.get(url, headers=headers or HEADERS, params=params, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"⚠️ Error solicitando {url}: {e}")
        return {}

# Adidas
def obtener_adidas(talla):
    productos = []
    for page in range(2):
        url = f"https://www.adidas.com.gt/api/catalog_system/pub/products/search?fq=productClusterIds:138&_from={page*50}&_to={(page+1)*50-1}"
        productos.extend(get_json(url))
    resultados = []
    for producto in productos:
        product_id = producto.get("productId")
        variaciones = get_json(f"https://www.adidas.com.gt/api/catalog_system/pub/products/variations/{product_id}")
        img = producto.get("items", [{}])[0].get("images", [{}])[0].get("imageUrl", "") if producto.get("items") else ""
        for sku in variaciones.get("skus", []):
            if talla in sku["dimensions"].get("Talla", ""):
                resultados.append({
                    "Producto": producto["productName"],
                    "Talla": sku["dimensions"]["Talla"],
                    "Precio": sku["bestPrice"] / 100,
                    "URL": f"https://www.adidas.com.gt/{producto.get('linkText')}/p",
                    "Imagen": img or "https://via.placeholder.com/240x200?text=Sneaker"
                })
    return resultados

# Meatpack y La Grieta
def obtener_shopify(url, tienda, talla):
    data = get_json(url)
    productos = []
    for prod in data.get("products", []):
        img = prod["images"][0]["src"] if prod.get("images") else "https://via.placeholder.com/240x200?text=Sneaker"
        for var in prod.get("variants", []):
            if talla in var.get("title", "") and var.get("available"):
                precio = float(var["price"]) / 100 if tienda == "Meatpack" else float(var["price"])
                productos.append({
                    "Tienda": tienda,
                    "Producto": prod["title"],
                    "Talla": var["title"],
                    "Precio": precio,
                    "URL": f"https://{url.split('/')[2]}/products/{prod['handle']}",
                    "Imagen": img
                })
    return productos

# Bitterheads
def obtener_bitterheads(talla, max_pages=3):
    productos = []
    for page in range(1, max_pages + 1):
        url = f"https://www.bitterheads.com/api/catalog_system/pub/products/search?fq=productClusterIds:159&ps=24&pg={page}"
        prods = get_json(url)
        for p in prods:
            variaciones = get_json(f"https://www.bitterheads.com/api/catalog_system/pub/products/variations/{p['productId']}")
            tallas = [sku["dimensions"]["Talla"] for sku in variaciones.get("skus", []) if sku.get("available")]
            if talla in tallas:
                img = p.get("items", [{}])[0].get("images", [{}])[0].get("imageUrl", "") if p.get("items") else ""
                productos.append({
                    "Producto": p["productName"],
                    "Talla": talla,
                    "Precio": p["items"][0]["sellers"][0]["commertialOffer"]["Price"],
                    "URL": f"https://www.bitterheads.com/{p['linkText']}/p",
                    "Imagen": img or "https://via.placeholder.com/240x200?text=Sneaker"
                })
    return productos

# Deportes del Centro
def obtener_deportesdelcentro(talla):
    productos = []
    for page in range(1, 6):
        data = get_json("https://deporteselcentro.com/wp-json/wc/store/v1/products", params={"page": page, "per_page": 100})
        for prod in data:
            tallas = [term["name"] for attr in prod["attributes"] if attr["name"].lower() == "talla" for term in attr["terms"]]
            if talla in tallas and prod.get("on_sale"):
                productos.append({
                    "Producto": prod["name"],
                    "Talla": talla,
                    "Precio": int(prod["prices"]["sale_price"]) / 100,
                    "URL": prod["permalink"],
                    "Imagen": prod.get("images", [{}])[0].get("src", "https://via.placeholder.com/240x200?text=Sneaker")
                })
    return productos

# Premium Trendy
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
                "Imagen": p.get("images", [{}])[0].get("src", "https://via.placeholder.com/240x200?text=Sneaker")
            })
        page += 1
    return productos

# Unificación
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
    df.to_csv("sneakers_output.csv", index=False)
    print(df)
