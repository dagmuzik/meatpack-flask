from scraping_tiendas import (
    obtener_meatpack, obtener_lagrieta, obtener_adidas_estandarizado,
    obtener_kicks, obtener_bitterheads, obtener_premiumtrendy,
    obtener_veinteavenida, obtener_deportesdelcentro
)
from utils import guardar_en_cache_local, guardar_en_cache_por_tienda, cargar_ultimo_cache

def es_sneaker(nombre):
    nombre = nombre.lower()
    keywords = ["sneaker", "zapatilla", "tenis", "runner", "air", "jordan", "yeezy", "forum", "ultraboost", "nmd", "suede", "nb", "sl 72", "gazelle", "stan smith", "vomero", "sk8", "old skool"]
    exclude = ["polo", "camiseta", "playera", "jersey", "short", "pantalón", "gorra", "guante", "calceta", "mochila", "bolsa", "protector", "balón", "sandalias"]
    return any(k in nombre for k in keywords) and not any(e in nombre for e in exclude)

def buscar_todos(talla="", tienda="", marca="", genero=""):
    productos = cargar_ultimo_cache()
    if not productos:
        return []

    # Normalizar claves si vienen en formato incorrecto (mayúsculas, etc.)
    productos_normalizados = []
    for p in productos:
        if "Producto" in p or "Precio" in p or "precio_final" in p:
            p = {k.lower(): v for k, v in p.items()}
        productos_normalizados.append(p)
        
    # Filtrar solo sneakers
    productos_normalizados = [p for p in productos_normalizados if es_sneaker(p.get("nombre", p.get("producto", "")).lower())]


    # Filtros básicos
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

    # Revisión y limpieza final
    productos_limpios = []
    for p in productos_normalizados:
        try:
            precio_raw = (
                p.get("precio") or
                p.get("precio_final") or
                p.get("precio_original") or
                p.get("Precio") or
                0
            )
            precio = float(precio_raw)
            if precio <= 0:
                continue
            p["precio"] = precio  # Clave estandarizada
            productos_limpios.append(p)
        except Exception as e:
            print(f"⚠️ Producto con error de precio: {p.get('nombre', 'sin nombre')} | Error: {e}")
            continue

    # Validar si hay productos válidos antes de construir el DataFrame
    if not productos_limpios:
        print("⚠️ No hay productos con precio válido para mostrar.")
        return []

    try:
        df = DataFrame(productos_limpios)
        if "precio" in df.columns:
            return df.sort_values(by="precio").to_dict("records")
        else:
            print("⚠️ No se encontró la columna 'precio' en el DataFrame.")
            return productos_limpios
    except Exception as e:
        print(f"❌ Error ordenando productos: {e}")
        return productos_limpios


def ejecutar_todo():
    productos = []
    productos += obtener_meatpack("")
    productos += obtener_lagrieta("")
    productos += obtener_adidas_estandarizado()
    productos += obtener_kicks("")
    productos += obtener_bitterheads()
    productos += obtener_premiumtrendy()
    productos += obtener_veinteavenida()
    productos += obtener_deportesdelcentro()
    guardar_en_cache_local(productos)
    guardar_en_cache_por_tienda(productos)
