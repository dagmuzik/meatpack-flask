import requests
from bs4 import BeautifulSoup

def detectar_marca(nombre):
    KNOWN_BRANDS = [
        "Nike", "Adidas", "Puma", "New Balance", "Vans", "Reebok",
        "Converse", "Under Armour", "Asics", "Saucony", "Salomon",
        "Jordan", "Mizuno", "Fila", "Hoka", "On"
    ]
    nombre_lower = nombre.lower()
    for marca in KNOWN_BRANDS:
        if marca.lower() in nombre_lower:
            return marca
    return nombre.split()[0]

def scrape_kicks_product(url_producto, talla_busqueda="9.5"):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url_producto, headers=headers, timeout=10)
        if response.status_code != 200:
            print("⚠️ No se pudo acceder al producto.")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        nombre = soup.select_one("h1.page-title span").text.strip() if soup.select_one("h1.page-title span") else "Producto sin nombre"
        imagen_tag = soup.select_one(".gallery-placeholder img")
        imagen = imagen_tag["src"] if imagen_tag else ""
        precio_tag = soup.select_one(".special-price .price") or soup.select_one(".price")
        precio = float(precio_tag.text.replace("Q", "").replace(",", "").strip()) if precio_tag else 0.0

        # 🆕 Tallas extraídas de manera robusta (usa data-option-label, aria-label o texto)
        tallas_disponibles = []
        for tag in soup.select(".swatch-option.text"):
            talla = (tag.get("data-option-label") or tag.get("aria-label") or tag.text).strip()
            if talla:
                tallas_disponibles.append(talla)

       if talla_busqueda.strip() not in [t.strip() for t in tallas_disponibles]:
    print(f"❌ Talla {talla_busqueda} no disponible.")
    return None

        return {
            "nombre": nombre,
            "marca": detectar_marca(nombre),
            "precio": precio,
            "imagen": imagen,
            "talla_disponible": talla_busqueda,
            "url": url_producto,
            "tallas_visibles": tallas_disponibles
        }

    except Exception as e:
        print(f"💥 Error: {e}")
        return None
