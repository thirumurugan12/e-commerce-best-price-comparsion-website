import requests, random, time, json
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://www.jiomart.com/",
    "Origin": "https://www.jiomart.com",
}

def search_jiomart(query, max_results=12):
    time.sleep(random.uniform(0.3, 0.8))
    # JioMart search URL
    url = f"https://www.jiomart.com/search#{requests.utils.quote(query)}"
    api_url = f"https://www.jiomart.com/api/products/search/v2?q={requests.utils.quote(query)}&page=1&pageSize=24"

    # Try their API first
    try:
        r = requests.get(api_url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()
        items = (data.get("products") or data.get("data", {}).get("products") or
                 data.get("result", {}).get("products") or [])
        if items:
            return _parse_api(items, max_results)
    except Exception as e:
        print(f"[JioMart] API error: {e}")

    # Fallback: scrape HTML
    return _scrape_html(query, max_results)


def _parse_api(items, max_results):
    products = []
    for item in items[:max_results]:
        try:
            title = item.get("name") or item.get("productName","N/A")
            price = str(item.get("price") or item.get("selling_price") or
                       item.get("discounted_price") or 0).replace(",","").replace("₹","").strip()
            if not price or price == "0": continue
            images = item.get("images") or [item.get("image","")]
            image = images[0] if isinstance(images, list) and images else str(images)
            slug = item.get("url") or item.get("slug","")
            url2 = slug if slug.startswith("http") else f"https://www.jiomart.com{slug}"
            products.append({"title":title,"price":price,"rating":"N/A","image":image,"url":url2,"source":"JioMart"})
        except: continue
    print(f"[JioMart] {len(products)} results (API)")
    return products


def _scrape_html(query, max_results):
    search_url = f"https://www.jiomart.com/catalogsearch/result/?q={requests.utils.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9",
    }
    try:
        r = requests.get(search_url, headers=headers, timeout=15); r.raise_for_status()
    except Exception as e:
        print(f"[JioMart HTML] {e}"); return []

    soup = BeautifulSoup(r.text, "lxml")
    cards = soup.find_all("li", class_="item") or soup.find_all("div", class_="product-item")
    products = []
    for card in cards[:max_results]:
        try:
            t = card.find("span", class_="clsgetname") or card.find("a", class_="product-item-link")
            title = t.get_text(strip=True) if t else "N/A"
            p = (card.find("span", class_="jm-body-xs") or
                 card.find("span", class_="price") or
                 card.find("div", class_="price-box"))
            if not p: continue
            price = p.get_text(strip=True).replace("₹","").replace(",","").replace("Rs.","").strip()
            price = ''.join(filter(lambda c: c.isdigit() or c == '.', price))
            if not price: continue
            img = card.find("img"); image = img.get("src") or img.get("data-src","") if img else ""
            lnk = card.find("a", href=True); pu = lnk["href"] if lnk else "https://www.jiomart.com"
            products.append({"title":title,"price":price,"rating":"N/A","image":image,"url":pu,"source":"JioMart"})
        except: continue
    print(f"[JioMart HTML] {len(products)} results")
    return products
