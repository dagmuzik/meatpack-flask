def get_kicks_products(talla_busqueda, min_price, max_price):
    import time
    import re
    import json
    from datetime import datetime
    from bs4 import BeautifulSoup
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import logging

    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = uc.Chrome(options=options)
    base_url = "https://www.kicks.com.gt"
    listing_url = f"{base_url}/sale-tienda"

    logging.info(f"🌐 Accediendo a: {listing_url}")
    driver.get(listing_url)

    time.sleep(4)  # Esperar carga de JS
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
            script_tag = prod_soup.find("script", type="text/x-magento-init")

            if script_tag:
                match = re.search(r'"jsonConfig"\s*:\s*({.*?"attributes".*?})\s*,\s*"template"', script_tag.text, re.DOTALL)
                match_simple = re.search(r'window.simpleProducts\s*=\s*({.*?});', driver.page_source, re.DOTALL)

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
                            if disponible and talla_busqueda in talla:
                                tallas_disponibles.append(talla)

            if tallas_disponibles and price is not None and min_price <= price <= max_price:
                products.append({
                    "marca": title.split()[0],
                    "nombre": title,
