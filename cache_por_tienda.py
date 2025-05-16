import os
import json
from datetime import datetime
from sneakerhunt import obtener_meatpack, obtener_lagrieta, obtener_adidas_estandarizado

def guardar_resultados(nombre, productos):
    os.makedirs("data", exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"data/cache_{nombre}_{now}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(productos, f, ensure_ascii=False, indent=2)
    print(f"✅ Cache guardado: {filename} ({len(productos)} productos)")
    return filename

def generar_cache_meatpack():
    productos = obtener_meatpack("")
    return guardar_resultados("meatpack", productos)

def generar_cache_lagrieta():
    productos = obtener_lagrieta("")
    return guardar_resultados("lagrieta", productos)

def generar_cache_adidas():
    productos = obtener_adidas_estandarizado()
    return guardar_resultados("adidas", productos)
