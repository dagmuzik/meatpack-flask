import glob
import json
import os
from sneakerhunt import obtener_shopify, obtener_adidas_estandarizado
from unificar_cache_total import unificar_caches_por_tienda

def guardar_resultados(nombre, productos):
    from datetime import datetime
    os.makedirs("data", exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"data/cache_{nombre}_{now}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(productos, f, ensure_ascii=False, indent=2)
    print(f"✅ Cache guardado: {filename} ({len(productos)} productos)")
    return filename

def ver_cache_total():
    archivos = sorted(glob.glob("data/cache_TOTAL_*.json"))
    if not archivos:
        return "❌ No hay archivos cache_TOTAL generados."

    ultimo = archivos[-1]
    with open(ultimo, encoding="utf-8") as f:
        data = json.load(f)
        return {
            "archivo": os.path.basename(ultimo),
            "total": len(data),
            "preview": data[:5]
        }

def generar_cache_meatpack():
    productos = obtener_shopify("https://meatpack.com/collections/special-price/products.json", "meatpack", talla="")
    guardar_resultados("meatpack", productos)
    return unificar_caches_por_tienda()

def generar_cache_lagrieta():
    productos = obtener_shopify("https://lagrieta.gt/collections/ultimas-tallas/products.json", "lagrieta", talla="")
    guardar_resultados("lagrieta", productos)
    return unificar_caches_por_tienda()

def generar_cache_adidas():
    productos = obtener_adidas_estandarizado()
    guardar_resultados("adidas", productos)
    return unificar_caches_por_tienda()
    
def generar_cache_kicks():
    from sneakerhunt import obtener_kicks
    productos = obtener_kicks("")
    from cache_por_tienda import guardar_resultados, unificar_caches_por_tienda
    guardar_resultados("kicks", productos)
    return unificar_caches_por_tienda()

def generar_cache_premiumtrendy():
    from sneakerhunt import obtener_premiumtrendy
    productos = obtener_premiumtrendy()  # Vacío para traer todos
    guardar_resultados("premiumtrendy", productos)
    return unificar_caches_por_tienda()
