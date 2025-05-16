import os
import glob
import json
from datetime import datetime

def unificar_caches_por_tienda():
    os.makedirs("data", exist_ok=True)
    patrones = ["data/cache_meatpack_*.json", "data/cache_lagrieta_*.json", "data/cache_adidas_*.json"]
    productos_totales = []

    for patron in patrones:
        archivos = sorted(glob.glob(patron))
        if archivos:
            ultimo = archivos[-1]
            try:
                with open(ultimo, encoding="utf-8") as f:
                    datos = json.load(f)
                    if isinstance(datos, list):
                        productos_totales.extend(datos)
            except Exception as e:
                print(f"⚠️ Error leyendo {ultimo}: {e}")

    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    salida = f"data/cache_TOTAL_{now}.json"
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(productos_totales, f, ensure_ascii=False, indent=2)

    print(f"✅ Cache total generado: {salida} ({len(productos_totales)} productos)")
    return salida
