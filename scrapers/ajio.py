import requests, random, time, json, re
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://www.ajio.com/",
    "Origin": "https://www.ajio.com",
    "x-px-original-token": "1",
}

def search_ajio(query, max_results=12):
    time.sleep(random.uniform(0.5, 1.0))
    # AJIO uses a REST search API
    api_url = (
        f"https://www.ajio.com/api/search?"
        f"text={requests.utils.quote(query)}&pageSize=24&currentPage=0"
        f"&sortBy=relevance&isBrandSearch=false&isFilter=false"
    )
    try:
        r = requests.get(api_url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()
        products_raw = (
            data.get("products") or
            data.get("searchResults", {}).get("products") or
            []
        )
        if products_raw:
            return _parse_api(products_raw, max_results)
    except Exception as e:
        print(f"[AJIO] API error: {e}")

    return _scrape_html(query, max_results)


def _parse_api(items, max_results):
    products = []
    for item in items[:max_results]:
        try:
            title = (item.get("name") or item.get("productName") or "N/A").strip()
            price_info = item.get("price") or {}
            if isinstance(price_info, dict):
                price = str(price_info.get("value") or price_info.get("selling") or 0)
            else:
                price = str(price_info)
            price = price.replace(",", "").replace("₹", "").strip()
            price = re.sub(r"[^\d.]", "", price)
            if not price or price == "0":
                continue
            # Image
            images = item.get("images") or []
            if images and isinstance(images[0], dict):
                image = images[0].get("url", "")
            elif images:
                image = str(images[0])
            else:
                image = item.get("image", "")
            if image and not image.startswith("http"):
                image = "https://assets.ajio.com" + image
            # URL
            code = item.get("code") or item.get("url") or ""
            url2 = f"https://www.ajio.com/{code}" if code and not code.startswith("http") else code
            # Rating
            rating = str(item.get("averageRating") or item.get("rating") or "N/A")
            products.append({"title": title, "price": price, "rating": rating,
                             "image": image, "url": url2, "source": "AJIO"})
        except Exception:
            continue
    print(f"[AJIO] {len(products)} results (API)")
    return products


def _scrape_html(query, max_results):
    url = f"https://www.ajio.com/search/?text={requests.utils.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        "Accept": "text/html,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9",
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"[AJIO HTML] {e}")
        return []

    soup = BeautifulSoup(r.text, "lxml")
    # Try embedded JSON first
    for script in soup.find_all("script"):
        txt = script.string or ""
        if '"products"' in txt and '"price"' in txt:
            try:
                start = txt.find("{")
                data = json.loads(txt[start:])
                items = _deep_find(data, "products") or []
                if items:
                    return _parse_api(items, max_results)
            except Exception:
                continue

    # HTML card fallback
    cards = soup.find_all("div", class_=re.compile(r"item|product|card", re.I))
    products = []
    for card in cards[:max_results * 2]:
        if len(products) >= max_results:
            break
        try:
            t = card.find(["h2", "h3", "p", "div"], class_=re.compile(r"name|title", re.I))
            title = t.get_text(strip=True) if t else None
            if not title or len(title) < 4:
                continue
            p = card.find(class_=re.compile(r"price|cost|amount", re.I))
            if not p:
                continue
            price = re.sub(r"[^\d.]", "", p.get_text(strip=True))
            if not price:
                continue
            img = card.find("img")
            image = (img.get("src") or img.get("data-src", "")) if img else ""
            lnk = card.find("a", href=True)
            href = lnk["href"] if lnk else ""
            url2 = href if href.startswith("http") else "https://www.ajio.com" + href
            products.append({"title": title, "price": price, "rating": "N/A",
                             "image": image, "url": url2, "source": "AJIO"})
        except Exception:
            continue
    print(f"[AJIO HTML] {len(products)} results")
    return products


def _deep_find(obj, key):
    if isinstance(obj, dict):
        if key in obj and isinstance(obj[key], list) and obj[key]:
            return obj[key]
        for v in obj.values():
            r = _deep_find(v, key)
            if r:
                return r
    elif isinstance(obj, list):
        for i in obj:
            r = _deep_find(i, key)
            if r:
                return r
    return None
