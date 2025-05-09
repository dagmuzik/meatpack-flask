# product_scraper.py
import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime

def get_kicks_products(talla_busqueda, min_price, max_price):
    base_url = "https://www.kicks.com.gt"
    listing_url = f"{base_url}/collections/sale?page=1"
    response = requests.get(listing_url)
    soup = BeautifulSoup(response.text, "html.parser")

    products = []
    product_links = list(set(a["href"] for a in soup.select("a.product-item-link") if a.get("href")))

    for link in product_links:
        full_url = base_url + link if link.startswith("/") else link
        res = requests.get(full_url)
        prod_soup = BeautifulSoup(res.text, "html.parser")
        script_tag = prod_soup.find("script", type="text/x-magento-init")

        title = prod_soup.find("h1", class_="page-title").get_text(strip=True) if prod_soup.find("h1", class_="page-title") else "No Title"
        price_tag = prod_soup.select_one("span.price")
        price = price_tag.get_text(strip=True).replace("Q", "") if price_tag else None
        price = float(price) if price and price.replace('.', '', 1).isdigit() else None
        image_tag = prod_soup.select_one("img.fotorama__img")
        image_url = image_tag["src"] if image_tag else ""

        tallas_disponibles = []
        if script_tag:
            try:
                match = re.search(r'"jsonConfig"\s*:\s*({.*?"attributes".*?})\s*,\s*"template"', script_tag.text, re.DOTALL)
                match_simple = re.search(r'window.simpleProducts\s*=\s*({.*?});', res.text, re.DOTALL)

                if match:
                    config_json = match.group(1)
                    config = json.loads(config_json)

                    disponibles = set()
                    if match_simple:
                        data = json.loads(match_simple.group(1))
                        disponibles = {str(item["id"]) for item in data.get("lines", [])}

                    for attr in config["attributes"].values():
                        for option in attr["options"]:
                            talla = option["label"]
                            ids = option.get("products", [])
                            disponible = any(pid in disponibles for pid in ids)
                            if disponible:
                                tallas_disponibles.append(talla)
            except Exception as e:
                print(f"⚠️ Error al procesar tallas en {full_url}: {e}")

        if tallas_disponibles and price is not None and min_price <= price <= max_price:
            products.append({
                "marca": title.split()[0],
                "nombre": title,
                "precio_final": price,
                "precio_original": None,
                "descuento": "",
                "tallas_disponibles": tallas_disponibles,
                "tienda": "KICKS",
                "url": full_url,
                "imagen": image_url
            })

    return products
