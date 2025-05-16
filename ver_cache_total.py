import glob
import json
import os

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
