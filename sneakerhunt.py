# ✅ Librerías necesarias
import os
import re
import time
import json
import glob
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pandas import DataFrame

__all__ = [
    "buscar_todos",
    "ejecutar_scraping_general",
    "obtener_ultimo_cache_tienda"
]

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

# ========== FUNCIONES DE UTILIDAD ==========
def get_json(url, headers=None, params=None, intentos=3):
    for intento in range(intentos):
        try:
            print(f"🌐 GET {url} (intento {intento + 1})")
            response = requests.get(url, headers=headers or HEADERS, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Error al obtener JSON desde {url}: {e}")
            time.sleep(2)
    return {}

def normalizar_talla(t):
    return re.sub(r"[^\d]", "", str(t))

def talla_coincide(talla_buscada, talla_encontrada):
    return normalizar_talla(talla_buscada) == normalizar_talla(talla_encontrada)

def inferir_marca(nombre):
    nombre = nombre.lower()
    if "sl 72" in nombre or "forum" in nombre or "gazelle" in nombre or "stan smith" in nombre:
        return "adidas"
    if "slip-on" in nombre or "sk8-hi" in nombre or "ultrarange" in nombre or "old skool" in nombre:
        return "vans"
    if "chuck" in nombre:
        return "converse"
    if "nike" in nombre or "air" in nombre or "kobe" in nombre or "jelly ma" in nombre:
        return "nike"
    if "new balance" in nombre:
        return "new balance"
    if "dellow" in nombre or "amiel" in nombre or "straye" in nombre:
        return "stepney workers club"
    if "shadow" in nombre or "grid azura" in nombre:
        return "saucony"
    if "nitro" in nombre:
        return "puma"
    return ""

def inferir_genero(nombre):
    nombre = nombre.lower()
    if any(palabra in nombre for palabra in [" hombre", " para hombre", " de hombre"]):
        return "hombre"
    if any(palabra in nombre for palabra in [" mujer", " para mujer", " de mujer"]):
        return "mujer"
    if "unisex" in nombre:
        return "unisex"
    return ""

# ========== FUNCIONES DE SCRAPING Y CACHE ==========

def guardar_en_cache_local(resultados, folder="data"):
    os.makedirs(folder, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = os.path.join(folder, f"cache_{now}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print(f"📝 Archivo guardado: {filename}")
    return filename

def scrap_raw_shopify():
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    os.makedirs("data", exist_ok=True)

    urls = {
        "meatpack": "https://meatpack.com/collections/special-price/products.json",
        "lagrieta": "https://lagrieta.gt/collections/ultimas-tallas/products.json"
    }

    for tienda, url in urls.items():
        data = get_json(url)
        file_path = f"data/raw_{tienda}_{now}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Guardado: {file_path}")

def obtener_meatpack(talla):
    return obtener_shopify("https://meatpack.com/collections/special-price/products.json", "meatpack", talla)

def obtener_lagrieta(talla):
    return obtener_shopify("https://lagrieta.gt/collections/ultimas-tallas/products.json", "lagrieta", talla)

def obtener_shopify(url, tienda, talla):
    from sneakerhunt import get_json, talla_coincide, inferir_genero, inferir_marca
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
                    print(f"â ï¸ Error al procesar producto {prod.get('title')}: {e}")
    return productos

def obtener_adidas_estandarizado():
    import requests
    productos = []
    page = 0
    paso = 50
    MAX_PAGES = 6  # Limitar a 300 productos aprox
    base_url = "https://www.adidas.com.gt/api/catalog_system/pub/products/search?fq=productClusterIds:138&_from={inicio}&_to={fin}"

    def get_variaciones(product_id):
        url = f"https://www.adidas.com.gt/api/catalog_system/pub/products/variations/{product_id}"
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            return res.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Error al obtener variaciones para producto {product_id}: {e}")
            return {}

    while True:
        if page >= MAX_PAGES:
            break

        url = base_url.format(inicio=page * paso, fin=(page + 1) * paso - 1)
        data = get_json(url)
        if not data:
            break

        for producto in data:
            product_id = producto.get("productId")
            variaciones = get_variaciones(product_id)
            items = producto.get("items", [])

            for item in items:
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
                            "marca": producto.get("brand", ""),
                            "genero": variaciones.get("Talle", {}).get(item.get("itemId"), "")
                        })
        page += 1

    print(f"✅ Adidas: {len(productos)} productos con stock y precio válido.")
    return productos

def obtener_kicks(talla_buscada=""):
    import re
    from bs4 import BeautifulSoup

    BASE_KICKS_API = "https://www.kicks.com.gt/rest/V1"
    BASE_KICKS_WEB = "https://www.kicks.com.gt"
    HEADERS = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    MAPA_GENERO = {
        "286": "hombre",
        "289": "mujer",
        "644": "niños"
    }

    # Paso 1: obtener SKUs desde la web
    skus = {}
    for pagina in range(1, 3):
        try:
            url = f"https://www.kicks.com.gt/marcas.html?p={pagina}&product_list_limit=36&special_price=29.99-1749.99&tipo_1=241"
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
            continue

    resultados = []
    for i, (sku_padre, href) in enumerate(skus.items()):
        padre_url = f"{BASE_KICKS_API}/products/{sku_padre}?storeCode=kicks_gt"
        data = get_json(padre_url)
        if not data or data.get("type_id") != "configurable":
            continue

        atributos = {attr["attribute_code"]: attr.get("value") for attr in data.get("custom_attributes", [])}
        nombre = data.get("name", "")
        url_key = atributos.get("url_key")
        url_producto = f"{BASE_KICKS_WEB}/{url_key}.html" if url_key else href

        imagen = None
        for attri in data.get("custom_attributes", []):
            if attri.get("attribute_code") == "image":
                imagen = f"https://www.kicks.com.gt/media/catalog/product{attri.get('value')}"
                break
        if not imagen:
            imagen = "https://via.placeholder.com/240x200?text=Sneaker"

        genero_id = atributos.get("genero")
        genero = MAPA_GENERO.get(genero_id, "")

        # Variantes
        variantes_url = f"{BASE_KICKS_API}/configurable-products/{sku_padre}/children?storeCode=kicks_gt"
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

def obtener_premiumtrendy():
    import requests
    import time

    BASE_URL = "https://premiumtrendygt.com"
    API_URL = f"{BASE_URL}/wp-json/wc/store/products"
    HEADERS = {"User-Agent": "Mozilla/5.0"}
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

                # Filtrar solo sneakers y evitar ropa
                if "sneakers" not in etiquetas or any(e in etiquetas for e in ["clothing", "true"]):
                    continue

                precios = prod.get("prices", {})
                regular = int(precios.get("regular_price", 0)) / 100
                oferta = int(precios.get("sale_price", 0)) / 100
                precio = oferta if oferta > 0 else regular
                if precio == 0:
                    continue

                # Extraer marca de atributos
                marca = ""
                for attr in prod.get("attributes", []):
                    if attr.get("name", "").lower() == "marca":
                        terms = attr.get("terms", [])
                        if terms:
                            marca = terms[0].get("name", "").strip().lower()
                            break

                # Extraer todas las tallas disponibles
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
                        "genero": ""  # No provee género
                    })

            except Exception as e:
                print(f"⚠️ Error procesando producto Premium Trendy: {e}")
                continue

        page += 1
        time.sleep(0.5)

    print(f"✅ Premium Trendy: {len(productos_disponibles)} productos disponibles.")
    return productos_disponibles

def obtener_bitterheads():
    import requests
    import time

    BASE_URL = "https://www.bitterheads.com"
    HEADERS = {"User-Agent": "Mozilla/5.0"}
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
        tallas_disponibles = []

        for sku in data.get("skus", []):
            if sku.get("available") and sku.get("availablequantity", 0) > 0:
                talla = sku.get("dimensions", {}).get("Talla", "")
                if talla:
                    tallas_disponibles.append(talla)

        return tallas_disponibles

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
                    "sku": "",  # No expuesto por la API
                    "nombre": nombre,
                    "precio": float(precio),
                    "talla": ", ".join(tallas_disponibles),
                    "imagen": imagen,
                    "link": link,
                    "tienda": "bitterheads",
                    "marca": marca.lower(),
                    "genero": ""  # No definido por ahora
                })

        time.sleep(0.5)

    print(f"✅ Bitterheads: {len(productos_data)} productos disponibles con stock.")
    return productos_data

def obtener_veinteavenida():
    import requests
    from bs4 import BeautifulSoup
    import time

    productos = []
    base_url = "https://veinteavenida.com/product-category/sale/page/"
    headers = {"User-Agent": "Mozilla/5.0"}

    for page in range(1, 4):
        print(f"📦 Veinte Avenida - Página {page}")
        url = f"{base_url}{page}/"
        try:
            res = requests.get(url, headers=headers, timeout=10)
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

                # Enriquecer producto
                detalle = requests.get(url_producto, headers=headers, timeout=10)
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
    import requests
    import os
    import json
    from datetime import datetime

    url = "https://deporteselcentro.com/wp-json/wc/store/products"
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://deporteselcentro.com/",
    "X-Requested-With": "XMLHttpRequest",
    "Accept-Language": "es-ES,es;q=0.9"
}

    page = 1
    productos = []

    while True:
        print(f"📦 Deportes del Centro - Página {page}")
        try:
            r = requests.get(url, headers=headers, params={"per_page": 100, "page": page}, timeout=15)
            if r.status_code != 200:
                print(f"❌ Error HTTP {r.status_code}")
                break
            data = r.json()
            if not data:
                break
        except Exception as e:
            print(f"❌ Error página {page}: {e}")
            break

        for p in data:
            try:
                nombre = p.get("name", "")
                precio = int(p.get("prices", {}).get("sale_price", 0)) / 100
                if precio == 0:
                    continue
                imagen = p.get("images", [{}])[0].get("src", "")
                link = p.get("permalink", "")
                sku = p.get("sku", "")
                tags = [t["name"].lower() for t in p.get("tags", [])]
                genero = "hombre" if "hombre" in tags else "mujer" if "mujer" in tags else ""
                marca = "nike" if "nike" in nombre.lower() else ""

                tallas = []
                for attr in p.get("attributes", []):
                    if attr.get("name", "").lower() == "talla":
                        tallas = [term.get("name") for term in attr.get("terms", [])]

                for talla in tallas:
                    productos.append({
                        "sku": sku,
                        "nombre": nombre,
                        "precio": precio,
                        "talla": talla,
                        "imagen": imagen,
                        "link": link,
                        "tienda": "deportesdelcentro",
                        "marca": marca,
                        "genero": genero
                    })

            except Exception as e:
                print(f"⚠️ Error procesando producto Deportes del Centro: {e}")
                continue

        page += 1

    print(f"✅ Deportes del Centro: {len(productos)} productos disponibles.")
    return productos


def generar_cache_estandar_desde_raw():
    def standardize_products(raw_products, tienda):
        standardized = []
        for product in raw_products:
            for variant in product.get("variants", []):
                if not variant.get("available"):
                    continue
                try:
                    entry = {
                        "sku": variant.get("sku"),
                        "nombre": product.get("title"),
                        "precio": float(variant.get("price") or 0),
                        "talla": variant.get("option1"),
                        "imagen": product.get("images", [{}])[0].get("src"),
                        "link": f"https://{tienda}.com/products/{product.get('handle')}",
                        "tienda": tienda,
                        "marca": next((tag for tag in product.get("tags", []) if tag.startswith("MARCA-")), ""),
                        "genero": next((tag for tag in product.get("tags", []) if tag.startswith("HOMBRE") or tag.startswith("MUJER") or tag.startswith("UNISEX")), "")
                    }
                    # Validación de precio
                    if entry["precio"] <= 0:
                        continue
                    # Unificar claves
                    entry = {k.lower(): v for k, v in entry.items()}
                    standardized.append(entry)
                except Exception as e:
                    print(f"⚠️ Error procesando producto de {tienda}: {e}")
        return standardized

    os.makedirs("data", exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    cache_file = f"data/cache_{now}.json"

    archivos_meat = sorted(glob.glob("data/raw_meatpack_*.json"))
    archivos_grieta = sorted(glob.glob("data/raw_lagrieta_*.json"))

    productos = []

    if archivos_meat:
        with open(archivos_meat[-1], encoding="utf-8") as f:
            productos += standardize_products(json.load(f).get("products", []), "meatpack")

    if archivos_grieta:
        with open(archivos_grieta[-1], encoding="utf-8") as f:
            productos += standardize_products(json.load(f).get("products", []), "lagrieta")

    print("🔍 Scrapeando Adidas...")
    productos += obtener_adidas_estandarizado()

    # 🔎 Verificación rápida de errores de precio
    invalids = [p for p in productos if not isinstance(p.get("precio"), (int, float))]
    if invalids:
        print(f"⚠️ {len(invalids)} productos sin precio válido.")
        for p in invalids[:5]:
            print(" -", p.get("nombre") or p.get("sku"), "| Precio:", p.get("precio"))

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(productos, f, ensure_ascii=False, indent=2)

    print(f"✅ Cache generado: {cache_file} ({len(productos)} productos)")


def ejecutar_todo():
    print("🚀 Ejecutando scrap + generar cache...")
    scrap_raw_shopify()
    generar_cache_estandar_desde_raw()

def cargar_ultimo_cache():
    import glob
    import json

    archivos = sorted(glob.glob("data/cache_TOTAL_*.json"))
    if not archivos:
        print("❌ No se encontró ningún archivo cache_TOTAL_*.json")
        return []

    try:
        with open(archivos[-1], encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else data.get("productos", [])
    except Exception as e:
        print(f"❌ Error al leer el cache: {e}")
        return []

def buscar_todos(talla="", tienda="", marca="", genero=""):
    productos = cargar_ultimo_cache()
    if not productos:
        return []

    # Normalizar nombres si algunos productos tienen claves en mayúscula
    productos_normalizados = []
    for p in productos:
        if "Producto" in p:
            p = {k.lower(): v for k, v in p.items()}
        productos_normalizados.append(p)

    # Filtros
    if talla:
        talla_norm = talla.strip().lower().replace(".", "").replace("us", "")
        productos_normalizados = [
            p for p in productos_normalizados
            if talla_norm in p.get("talla", "").lower().replace(".", "").replace("us", "")
        ]

    if tienda:
        productos_normalizados = [
            p for p in productos_normalizados
            if p.get("tienda", "").lower() == tienda.lower()
        ]

    if marca:
        productos_normalizados = [
            p for p in productos_normalizados
            if p.get("marca", "").lower() == marca.lower()
        ]

    if genero:
        productos_normalizados = [
            p for p in productos_normalizados
            if p.get("genero", "").lower() == genero.lower()
        ]

    productos_limpios = []
    for p in productos_normalizados:
        try:
            precio_raw = p.get("precio") or p.get("Precio") or 0
            precio = float(precio_raw)
            if precio <= 0:
                continue
            p["precio"] = precio
            productos_limpios.append(p)
        except Exception as e:
            print(f"⚠️ Producto con error de precio: {p.get('nombre', 'sin nombre')} | Error: {e}")
            continue

    try:
        df = DataFrame(productos_limpios)
        return df.sort_values(by="precio").to_dict("records")
    except Exception as e:
        print(f"❌ Error ordenando productos: {e}")
        return productos_limpios

        
import glob
import os

def obtener_ultimo_cache_tienda(tienda):
    import glob
    import os

    patrones = {
        "meatpack": "data/cache_meatpack_*.json",
        "lagrieta": "data/cache_lagrieta_*.json",
        "adidas": "data/cache_adidas_*.json",
        "premiumtrendy": "data/cache_premiumtrendy_*.json",
        "kicks": "data/cache_kicks_*.json",
        "bitterheads": "data/cache_bitterheads_*.json",
        "veinteavenida": "data/cache_veinteavenida_*.json",
        "deportesdelcentro": "data/cache_deportesdelcentro_*.json"
    }

    patron = patrones.get(tienda.lower())
    if not patron:
        return None

    archivos = sorted(glob.glob(patron))
    if not archivos:
        return None

    return archivos[-1]

