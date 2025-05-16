import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time

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

def guardar_en_cache_local(resultados, folder="data"):
    import os
    from datetime import datetime
    import json

    os.makedirs(folder, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = os.path.join(folder, f"cache_{now}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "productos": resultados
        }, f, ensure_ascii=False, indent=2)
    print(f"📝 Archivo guardado: {filename}")
    return filename

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
    if "slip-on" in nombre or "sk8-hi" in nombre or "ultrarange" in nombre or "old Skool" in nombre:
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

    # Detectar Hombre
    if any(palabra in nombre for palabra in [" hombre", " para hombre", " de hombre"]):
        return "hombre"

    # Detectar Mujer
    if any(palabra in nombre for palabra in [" mujer", " para mujer", " de mujer"]):
        return "mujer"

    # Detectar Unisex
    if "unisex" in nombre:
        return "unisex"

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
    return obtener_shopify("https://meatpack.com/collections/special-price/products.json", "Meatpack", talla)

def obtener_lagrieta(talla):
    return obtener_shopify("https://lagrieta.gt/collections/ultimas-tallas/products.json", "La Grieta", talla)

def obtener_premiumtrendy(talla):
    import requests

    headers = {"User-Agent": "Mozilla/5.0"}
    base_url = "https://premiumtrendygt.com"
    api_url = f"{base_url}/wp-json/wc/store/products"
    productos_disponibles = []
    talla_buscada = talla.replace(".", "-").strip()
    page = 1

    while True:
        try:
            response = requests.get(api_url, headers=headers, params={
                "on_sale": "true",
                "per_page": 100,
                "page": page
            }, timeout=10)

            if response.status_code != 200:
                break

            productos = response.json()
            if not isinstance(productos, list) or not productos:
                break

        except Exception as e:
            break

        for prod in productos:
            try:
                nombre = prod.get("name", "")
                url = prod.get("permalink", "")
                variaciones = prod.get("variations", [])
                imagen = prod.get("images", [{}])[0].get("src", "https://via.placeholder.com/240x200?text=Sneaker")
                etiquetas = {tag.get("name", "").lower() for tag in prod.get("tags", [])}

                if "sneakers" not in etiquetas or etiquetas & {"clothing", "hombre", "ralph lauren", "true"}:
                    continue

                precios = prod.get("prices", {})
                regular = int(precios.get("regular_price", 0)) / 100
                oferta = int(precios.get("sale_price", 0)) / 100
                precio_final = oferta if oferta > 0 else regular

                if precio_final == 0:
                    continue

                talla_encontrada = False
                for var in variaciones:
                    for attr in var.get("attributes", []):
                        if "talla" in attr.get("name", "").lower() and attr.get("value", "").strip() == talla_buscada:
                            talla_encontrada = True
                            break
                    if talla_encontrada:
                        break

                if talla_encontrada:
                    productos_disponibles.append({
                        "Producto": nombre,
                        "Talla": talla,
                        "Precio": precio_final,
                        "URL": url,
                        "Imagen": imagen,
                        "Tienda": "Premium Trendy",
                        "Marca": inferir_marca(nombre)
                    })

            except Exception as e:
                continue

        page += 1

    return productos_disponibles
        
def obtener_veinteavenida(talla):
    import time

    base_url = "https://veinteavenida.com"
    productos = []
    for page in range(1, 4):
        url = f"{base_url}/product-category/sale/page/{page}/"
        try:
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if res.status_code != 200:
                print(f"❌ No se pudo cargar página {page}")
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

                # Cargar detalles individuales
                try:
                    detalle = requests.get(url_producto, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                    detalle_soup = BeautifulSoup(detalle.text, "html.parser")

                    precios = detalle_soup.select("p.price span.woocommerce-Price-amount")
                    if len(precios) >= 2:
                        precio_final = precios[1].text.strip().replace("Q", "").replace(",", "")
                    elif len(precios) == 1:
                        precio_final = precios[0].text.strip().replace("Q", "").replace(",", "")
                    else:
                        continue

                    try:
                        precio_float = float(precio_final)
                    except:
                        continue

                    tallas = []
                    for div in detalle_soup.select(".tfwctool-varation-swatch-preview"):
                        talla_html = div.get("data-bs-original-title") or div.text.strip()
                        if talla_coincide(talla, talla_html):
                            tallas.append(talla_html)

                    if not tallas:
                        continue

                    productos.append({
                        "Producto": nombre,
                        "Talla": ", ".join(tallas),
                        "Precio": precio_float,
                        "URL": url_producto,
                        "Imagen": imagen,
                        "Tienda": "Veinte Avenida",
                        "Marca": inferir_marca(nombre),
                        "Genero": inferir_genero(nombre)
                    })
                except Exception as e:
                    print(f"⚠️ Error enriqueciendo {nombre}: {e}")
            except:
                continue

        time.sleep(0.5)

    return productos
        
def obtener_bitterheads(talla):
    import time

    url_base = "https://www.bitterheads.com"
    search_url = f"{url_base}/api/catalog_system/pub/products/search?fq=specificationFilter_43:*&fq=specificationFilter_110:*&_from=0&_to=49"
    productos = get_json(search_url)
    resultados = []

    for p in productos:
        time.sleep(0.1)  # pausa para evitar saturación de requests

        try:
            tallas_disp = get_json(f"{url_base}/api/catalog_system/pub/products/variations/{p['productId']}")
            tallas = []
            for sku in tallas_disp.get("skus", []):
                stock = sku.get("availableQuantity", 0)
                talla_actual = sku.get("dimensions", {}).get("Talla")
                if stock > 0 and talla_coincide(talla, talla_actual):
                    tallas.append(talla_actual)

            if not tallas:
                continue

            precio = int(p["items"][0]["sellers"][0]["commertialOffer"]["Price"])
            imagen = p.get("items", [{}])[0].get("images", [{}])[0].get("imageUrl", "")
            if not imagen:
                imagen = "https://via.placeholder.com/240x200?text=Sneaker"

            resultados.append({
                "Producto": p["productName"],
                "Talla": ", ".join(tallas),
                "Precio": precio,
                "URL": f'{url_base}/{p["linkText"]}/p',
                "Imagen": imagen,
                "Tienda": "Bitterheads",
                "Marca": inferir_marca(p["productName"]),
                "Genero": inferir_genero(p["productName"])
            })

        except Exception as e:
            print(f"⚠️ Error al procesar producto {p.get('productName')}: {e}")

    return resultados

import requests

def obtener_adidas_estandarizado():
    productos = []
    page = 0
    paso = 50
    base_url = "https://www.adidas.com.gt/api/catalog_system/pub/products/search?fq=productClusterIds:138&_from={inicio}&_to={fin}"

    def get_json(url):
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"❌ Error GET {url}: {e}")
            return []

    def get_variaciones(product_id):
        url = f"https://www.adidas.com.gt/api/catalog_system/pub/products/variations/{product_id}"
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"❌ Error al obtener variaciones de {product_id}: {e}")
            return {}

    while True:
        url = base_url.format(inicio=page*paso, fin=(page+1)*paso - 1)
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

def buscar_todos(talla="", tienda="", marca="", genero=""):
    from pandas import DataFrame

    print(f"\n🔎 Buscando productos talla {talla or '[cualquiera]'} en tienda: {tienda or 'Todas'} con marca: {marca or 'Todas'} con género: {genero or 'Todos'}")

    resultados = []

def agregar(funcion, nombre):
    try:
        print(f"🔍 Revisando {nombre}...")
        datos = funcion(talla)
        print(f"🔎 {nombre} devolvió {len(datos)} productos")
        for p in datos[:5]:  # mostrar solo los primeros 5 productos
            print(f" → {p.get('Producto')}")
            print(f"   Precio: {p.get('Precio')} ({type(p.get('Precio'))})")
            print(f"   Talla: {p.get('Talla')}")
            print(f"   Tienda: {p.get('Tienda')}")
            print(" ")
        resultados.extend(datos)
    except Exception as e:
        print(f"❌ Error en {nombre}: {e}")

    if tienda in ("", "Adidas"):
        agregar(obtener_adidas, "Adidas")

    #if tienda in ("", "Kicks"):
    #    agregar(obtener_kicks, "Kicks")

    #if tienda in ("", "Bitterheads"):
    #    agregar(obtener_bitterheads, "Bitterheads")

    if tienda in ("", "Meatpack"):
        agregar(obtener_meatpack, "Meatpack")

    if tienda in ("", "La Grieta"):
        agregar(obtener_lagrieta, "La Grieta")

    #if tienda in ("", "Premium Trendy"):
    #    agregar(obtener_premiumtrendy, "Premium Trendy")

    #if tienda in ("", "Veinte Avenida"):
    #    agregar(obtener_veinteavenida, "Veinte Avenida")

    # 🔍 Filtros adicionales
    if marca:
        marca = marca.strip().lower()
        resultados = [p for p in resultados if p.get("Marca", "").lower() == marca]

    if genero:
        genero = genero.strip().lower()
        resultados = [p for p in resultados if p.get("Genero", "").lower() == genero]

    try:
        from datetime import datetime

        # 🔍 Diagnóstico: detectar productos sin Precio válido
        productos_sin_precio = [p for p in resultados if not isinstance(p.get("Precio"), (int, float))]
        if productos_sin_precio:
            print(f"⚠️ {len(productos_sin_precio)} productos sin Precio válido:")
            for p in productos_sin_precio[:5]:  # mostramos solo los primeros 5
                print(f" → {p.get('Producto')} (Tienda: {p.get('Tienda')}, Precio: {p.get('Precio')})")

            # 💾 Guardar para inspección web
            os.makedirs("data", exist_ok=True)
            now = datetime.now().strftime("%Y-%m-%d_%H-%M")
            ruta_error = f"data/errores_sin_precio_{now}.json"
            with open(ruta_error, "w", encoding="utf-8") as f:
                json.dump(productos_sin_precio, f, ensure_ascii=False, indent=2)
            print(f"🛠 Archivo con errores guardado en: {ruta_error}")

        # ✅ Usamos solo los que sí tienen precio
        resultados_validos = [p for p in resultados if isinstance(p.get("Precio"), (int, float))]
        if not resultados_validos:
            print("⚠️ No se encontraron productos con precios válidos.")
            return []

        df = DataFrame(resultados_validos)
        return df.sort_values(by="Precio").to_dict("records")

    except Exception as e:
        print("❌ Error al convertir y ordenar resultados:", e)
        return resultados

import os
import json
from glob import glob
from datetime import datetime

# ... tus imports y funciones existentes ...

def ejecutar_scraping_general():
    print("⏳ Ejecutando scraping desde función externa (cron)")
    resultados = buscar_todos(talla="")
    guardar_en_cache_local(resultados)

if __name__ == "__main__":
    print("⏳ Ejecutando scraping automático sin filtrar por talla")
    resultados = buscar_todos(talla="")  # sin filtro
    print(f"✅ Productos encontrados: {len(resultados)}")

    archivo_reciente = guardar_en_cache_local(resultados)

    archivo_anterior = obtener_cache_anterior(archivo_reciente)
    if archivo_anterior:
        anteriores = cargar_archivo(archivo_anterior)
        nuevos = identificar_nuevos(anteriores, resultados)

        if nuevos:
            print(f"🆕 Nuevos productos detectados: {len(nuevos)}")
            for p in nuevos[:10]:
                print(f"- {p['Producto']} ({p.get('Tienda', '')}) ➜ {p['URL']}")

            nombre_nuevos = archivo_reciente.replace("cache_", "nuevos_")
            with open(nombre_nuevos, "w", encoding="utf-8") as f:
                json.dump(nuevos, f, ensure_ascii=False, indent=2)
            print(f"📦 Nuevos productos guardados en: {nombre_nuevos}")
        else:
            print("🟨 Sin productos nuevos.")
    else:
        print("⚠️ Primer archivo: no hay comparación disponible.")

import requests
import json
import os
from datetime import datetime
import glob

# ========== FUNCIONES ==========

def scrap_raw_shopify():
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    os.makedirs("data", exist_ok=True)

    def get_json(url):
        try:
            print(f"🌐 GET {url}")
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"❌ Error al obtener {url}: {e}")
            return {}

    # MEATPACK
    url_meatpack = "https://meatpack.com/collections/special-price/products.json"
    data_meatpack = get_json(url_meatpack)
    with open(f"data/raw_meatpack_{now}.json", "w", encoding="utf-8") as f:
        json.dump(data_meatpack, f, ensure_ascii=False, indent=2)
    print(f"✅ Guardado: data/raw_meatpack_{now}.json")

    # LA GRIETA
    url_grieta = "https://lagrieta.gt/collections/ultimas-tallas/products.json"
    data_grieta = get_json(url_grieta)
    with open(f"data/raw_lagrieta_{now}.json", "w", encoding="utf-8") as f:
        json.dump(data_grieta, f, ensure_ascii=False, indent=2)
    print(f"✅ Guardado: data/raw_lagrieta_{now}.json")

def generar_cache_estandar_desde_raw():
    def standardize_products(raw_products, tienda):
        standardized = []
        for product in raw_products:
            for variant in product.get("variants", []):
                if not variant.get("available"):
                    continue
                entry = {
                    "sku": variant.get("sku"),
                    "nombre": product.get("title"),
                    "precio": float(variant.get("price")),
                    "talla": variant.get("option1"),
                    "imagen": product.get("images", [{}])[0].get("src"),
                    "link": f"https://{tienda}.com/products/{product.get('handle')}",
                    "tienda": tienda,
                    "marca": next((tag for tag in product.get("tags", []) if tag.startswith("MARCA-")), ""),
                    "genero": next((tag for tag in product.get("tags", []) if tag.startswith("HOMBRE") or tag.startswith("MUJER") or tag.startswith("UNISEX")), "")
                }
                standardized.append(entry)
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

# ✅ Agregar Adidas usando nueva función estandarizada
from obtener_adidas_estandarizado import obtener_adidas_estandarizado

print("🔍 Scrapeando Adidas...")
productos += obtener_adidas_estandarizado()

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(productos, f, ensure_ascii=False, indent=2)

    print(f"✅ Cache generado: {cache_file} ({len(productos)} productos)")

def ejecutar_todo():
    print("🚀 Ejecutando scrap + generar cache...")
    scrap_raw_shopify()
    generar_cache_estandar_desde_raw()

# ========== FUNCIONES INTEGRADAS ==========

import requests

def obtener_adidas_estandarizado():
    productos = []
    page = 0
    paso = 50
    base_url = "https://www.adidas.com.gt/api/catalog_system/pub/products/search?fq=productClusterIds:138&_from={inicio}&_to={fin}"

    def get_json(url):
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"❌ Error GET {url}: {e}")
            return []

    def get_variaciones(product_id):
        url = f"https://www.adidas.com.gt/api/catalog_system/pub/products/variations/{product_id}"
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"❌ Error al obtener variaciones de {product_id}: {e}")
            return {}

    while True:
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


def generar_cache_estandar_desde_raw():
    import os
    import json
    import glob
    from datetime import datetime

    def standardize_products(raw_products, tienda):
        standardized = []
        for product in raw_products:
            for variant in product.get("variants", []):
                if not variant.get("available"):
                    continue
                entry = {
                    "sku": variant.get("sku"),
                    "nombre": product.get("title"),
                    "precio": float(variant.get("price")),
                    "talla": variant.get("option1"),
                    "imagen": product.get("images", [{}])[0].get("src"),
                    "link": f"https://{tienda}.com/products/{product.get('handle')}",
                    "tienda": tienda,
                    "marca": next((tag for tag in product.get("tags", []) if tag.startswith("MARCA-")), ""),
                    "genero": next((tag for tag in product.get("tags", []) if tag.startswith("HOMBRE") or tag.startswith("MUJER") or tag.startswith("UNISEX")), "")
                }
                standardized.append(entry)
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

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(productos, f, ensure_ascii=False, indent=2)

    print(f"✅ Cache generado: {cache_file} ({len(productos)} productos)")

def ejecutar_todo():
    print("🚀 Ejecutando scrap + generar cache...")
    scrap_raw_shopify()
    generar_cache_estandar_desde_raw()
