def comparar_caches_y_generar_nuevos():
    import os
    import json
    from datetime import datetime

    def cargar_productos(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def producto_es_nuevo(prod, productos_anteriores):
        claves = ("sku", "nombre", "talla", "tienda")
        for antiguo in productos_anteriores:
            if all(prod.get(k) == antiguo.get(k) for k in claves):
                return False
        return True

    carpeta = "data"
    archivos = sorted(
        [f for f in os.listdir(carpeta) if f.startswith("cache_TOTAL_") and f.endswith("_unificado.json")]
    )

    if len(archivos) < 2:
        print("❌ Se necesitan al menos dos archivos cache_TOTAL para comparar.")
        return

    anterior, actual = archivos[-2], archivos[-1]
    productos_anteriores = cargar_productos(os.path.join(carpeta, anterior))
    productos_actuales = cargar_productos(os.path.join(carpeta, actual))

    nuevos = [p for p in productos_actuales if producto_es_nuevo(p, productos_anteriores)]

    if nuevos:
        salida = f"productos_nuevos_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.json"
        path_salida = os.path.join(carpeta, salida)
        with open(path_salida, "w", encoding="utf-8") as f:
            json.dump(nuevos, f, ensure_ascii=False, indent=2)

        print(f"✅ Se encontraron {len(nuevos)} productos nuevos.")
        print(f"📁 Archivo generado: {path_salida}")
    else:
        print("ℹ️ No se encontraron productos nuevos. No se generó archivo.")

if __name__ == "__main__":
    comparar_caches_y_generar_nuevos()
