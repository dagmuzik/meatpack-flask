# product_scraper.py

import time
import re
import json
import logging
import tempfile
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_kicks_products(talla_busqueda, min_price, max_price):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")  # Evita colisión de sesiones

    driver = webdriver.Chrome(options=options)
    base_url = "https://www.kicks.com.gt"
    listing_url = f"{base_url}/sale-tienda"

    logging.info(f"🌐 Accediendo a: {listing_url}")
    driver.get(listing_url)
    time.sleep(4)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = []

    product_links = list(set(a["href"] for a in soup.select("a.product-item-link") if a.get("href")))

    for link in product_links:
        full_url = base_url + link if link.startswith("/") else link
        try:
            driver.get(full_url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.page-title")))
            prod_soup = BeautifulSoup(driver.page_source, "html.parser")

            title = prod_soup.find("h1", class_="page-title").get_text(strip=True)
            price_tag = prod_soup.select_one("span.price")
            price = price_tag.get_text(strip=True).replace("Q", "") if price_tag else None
            price = float(price) if price and price.replace('.', '', 1).isdigit() else None
            image_tag = prod_soup.select_one("img.fotorama__img")
            image_url = image_tag["src"] if image_tag else ""

            tallas_disponibles = []
            buttons = prod_soup.select("div.swatch-option.text")

            for btn in buttons:
                label = btn.get("aria-label", "").strip()
                aria_checked = btn.get("aria-checked", "")
                if talla_busqueda in label and aria_checked == "false":
                    tallas_disponibles.append(label)

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

        except Exception as e:
            logging.warning(f"⚠️ Error al procesar {full_url}: {e}")
            continue

    driver.quit()
    return products
