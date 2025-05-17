def unificar_caches_por_tienda():
    import os
    import glob
    import json
    from datetime import datetime

    os.makedirs("data", exist_ok=True)
    patrones = [
    "data/cache_meatpack_*.json",
    "data/cache_lagrieta_*.json",
    "data/cache_adidas_*.json",
    "data/cache_premiumtrendy_*.json",
    "data/cache_kicks_*.json",
    "data/cache_bitterheads_*.json"
    ]
    productos_totales = []

    for patron in patrones:
        archivos = sorted(glob.glob(patron))
        if archivos:
            ultimo = archivos[-1]
            try:
                with open(ultimo, encoding="utf-8") as f:
                    datos = json.load(f)
                    if not isinstance(datos, list):
                        continue
                    for p in datos:
                        try:
                            producto = {
                                "sku": p.get("sku") or "",
                                "nombre": p.get("nombre") or p.get("Producto", ""),
                                "precio": float(p.get("precio") or p.get("Precio")),
                                "talla": p.get("talla") or p.get("Talla", ""),
                                "imagen": p.get("imagen") or p.get("Imagen", ""),
                                "link": p.get("link") or p.get("URL", ""),
                                "tienda": (p.get("tienda") or p.get("Tienda", "")).lower(),
                                "marca": (p.get("marca") or p.get("Marca", "")).replace("MARCA-", "").lower(),
                                "genero": (p.get("genero") or p.get("Genero", "")).lower()
                            }
                            productos_totales.append(producto)
                        except Exception as e:
                            print(f"⚠️ Producto con error en {ultimo}: {e}")
            except Exception as e:
                print(f"⚠️ Error leyendo {ultimo}: {e}")

    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    salida = f"data/cache_TOTAL_{now}_unificado.json"
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(productos_totales, f, ensure_ascii=False, indent=2)

    print(f"✅ Cache total generado: {salida} ({len(productos_totales)} productos)")
    return salida
