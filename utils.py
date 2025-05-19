# utils.py
import glob
import os
import re
import time
import json
import requests
from datetime import datetime

# Encabezados HTTP comunes
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://deporteselcentro.com/",
    "Accept-Language": "es-ES,es;q=0.9"
}


# Mapa de IDs de tallas a texto legible
MAPA_TALLAS = {
    "139": "5.5", "142": "5.75", "145": "6", "148": "6.5", "151": "7", "154": "7.5",
    "157": "8", "160": "8.5", "163": "9", "166": "9.5", "169": "10", "172": "10.5",
    "175": "11", "178": "11.5", "181": "12", "184": "12.5", "187": "13", "190": "13.5",
    "193": "14", "196": "14.5", "199": "15", "752": "15.5?"
}

def get_json(url, headers=None, params=None, intentos=3):
    """Obtiene JSON desde una URL con reintentos"""
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
    """Elimina caracteres no numéricos de una talla"""
    return re.sub(r"[^\d]", "", str(t))

def talla_coincide(talla_buscada, talla_encontrada):
    """Compara tallas ignorando puntos, letras u otros caracteres"""
    return normalizar_talla(talla_buscada) == normalizar_talla(talla_encontrada)

def inferir_marca(nombre):
    """Intenta inferir la marca del producto desde su nombre"""
    nombre = nombre.lower()
    if any(m in nombre for m in ["sl 72", "forum", "gazelle", "stan smith"]):
        return "adidas"
    if any(m in nombre for m in ["slip-on", "sk8-hi", "ultrarange", "old skool"]):
        return "vans"
    if "chuck" in nombre:
        return "converse"
    if any(m in nombre for m in ["nike", "air", "kobe", "jelly ma"]):
        return "nike"
    if "new balance" in nombre:
        return "new balance"
    if any(m in nombre for m in ["dellow", "amiel", "straye"]):
        return "stepney workers club"
    if any(m in nombre for m in ["shadow", "grid azura"]):
        return "saucony"
    if "nitro" in nombre:
        return "puma"
    return ""

def inferir_genero(nombre):
    """Intenta inferir el género del producto desde su nombre"""
    nombre = nombre.lower()
    if any(p in nombre for p in [" hombre", " para hombre", " de hombre"]):
        return "hombre"
    if any(p in nombre for p in [" mujer", " para mujer", " de mujer"]):
        return "mujer"
    if "unisex" in nombre:
        return "unisex"
    return ""

def guardar_en_cache_local(productos, folder="data"):
    os.makedirs(folder, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = os.path.join(folder, f"cache_TOTAL_{now}.json")  # <-- el nombre que espera app.py
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(productos, f, ensure_ascii=False, indent=2)
    print(f"📝 Archivo guardado: {filename}")
    return filename

def guardar_en_cache_por_tienda(productos, folder="data"):
    os.makedirs(folder, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    tiendas = set(p["tienda"] for p in productos if "tienda" in p)
    for tienda in tiendas:
        filtrados = [p for p in productos if p.get("tienda") == tienda]
        filename = os.path.join(folder, f"cache_{now}_{tienda.lower()}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(filtrados, f, ensure_ascii=False, indent=2)
        print(f"📦 Guardado: {filename}")

def obtener_ultimos_nuevos(path="data"):
    archivos = sorted(glob.glob(f"{path}/nuevos_*.json"))
    if not archivos:
        return []
    with open(archivos[-1], encoding="utf-8") as f:
        return json.load(f)

def obtener_ultimo_cache_tienda(tienda, path="data"):
    archivos = sorted(glob.glob(f"{path}/cache_*_{tienda}.json"))
    return archivos[-1] if archivos else None

def cargar_ultimo_cache(path="data"):
    archivos = sorted(glob.glob(f"{path}/cache_TOTAL_*.json"))
    if not archivos:
        print("⚠️ No se encontró ningún archivo cache_TOTAL.")
        return []
    with open(archivos[-1], encoding="utf-8") as f:
        return json.load(f)
