import requests, random, time, json, re
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://www.tatacliq.com/",
    "Origin": "https://www.tatacliq.com",
}


def search_tatacliq(query, max_results=12):
    time.sleep(random.uniform(0.5, 1.0))
    # Tata CLiQ GraphQL / REST search API
    api_url = (
        f"https://www.tatacliq.com/moglilayer/api/v1/page/search/search-results"
        f"?searchText={requests.utils.quote(query)}&isTextSearch=true"
        f"&page=0&pageSize=24&outOfStock=false&dchannel=WEB"
    )
    try:
        r = requests.get(api_url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()
        items = (
            data.get("searchData", {}).get("clpProductListVO", []) or
            data.get("products") or
            data.get("data", {}).get("products") or
            []
        )
        if items:
            return _parse_api(items, max_results)
    except Exception as e:
        print(f"[TataCLiQ] API error: {e}")

    return _scrape_html(query, max_results)


def _parse_api(items, max_results):
    products = []
    for item in items[:max_results]:
        try:
            title = (
                item.get("productName") or item.get("name") or
                item.get("shortDescription") or "N/A"
            ).strip()
            price_map = item.get("priceInfo") or item.get("price") or {}
            if isinstance(price_map, dict):
                price = str(
                    price_map.get("sellingPrice") or
                    price_map.get("discountedPrice") or
                    price_map.get("mrp") or 0
                )
            else:
                price = str(price_map)
            price = re.sub(r"[^\d.]", "", price.replace(",", ""))
            if not price or price == "0":
                continue
            # Image
            img_info = item.get("images") or item.get("image") or []
            if isinstance(img_info, list) and img_info:
                first = img_info[0]
                image = first.get("imageURL") or first.get("url") or str(first) if isinstance(first, dict) else str(first)
            elif isinstance(img_info, dict):
                image = img_info.get("imageURL") or img_info.get("url") or ""
            else:
                image = str(img_info) if img_info else ""
            if image and not image.startswith("http"):
                image = "https://apcache.tatacliq.com" + image
            # URL
            slug = item.get("productURL") or item.get("slug") or item.get("canonicalUrl") or ""
            url2 = slug if slug.startswith("http") else "https://www.tatacliq.com" + slug
            # Rating
            rating = str(item.get("averageRating") or item.get("rating") or "N/A")
            products.append({"title": title, "price": price, "rating": rating,
                             "image": image, "url": url2, "source": "TataCLiQ"})
        except Exception:
            continue
    print(f"[TataCLiQ] {len(products)} results (API)")
    return products


def _scrape_html(query, max_results):
    url = f"https://www.tatacliq.com/search/?searchCategory=all&q={requests.utils.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
        "Accept": "text/html,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9",
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"[TataCLiQ HTML] {e}")
        return []

    soup = BeautifulSoup(r.text, "lxml")
    # Try embedded JSON
    for script in soup.find_all("script", type="application/json"):
        txt = script.string or ""
        if "productName" in txt or "sellingPrice" in txt:
            try:
                data = json.loads(txt)
                items = _deep_find(data, "clpProductListVO") or _deep_find(data, "products") or []
                if items:
                    return _parse_api(items, max_results)
            except Exception:
                continue

    # HTML card fallback
    cards = (
        soup.find_all("div", class_=re.compile(r"ProductModule|product-card|ProductCard", re.I)) or
        soup.find_all("li", class_=re.compile(r"product", re.I))
    )
    products = []
    for card in cards[:max_results * 2]:
        if len(products) >= max_results:
            break
        try:
            t = card.find(class_=re.compile(r"name|title|product", re.I))
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
            url2 = href if href.startswith("http") else "https://www.tatacliq.com" + href
            products.append({"title": title, "price": price, "rating": "N/A",
                             "image": image, "url": url2, "source": "TataCLiQ"})
        except Exception:
            continue
    print(f"[TataCLiQ HTML] {len(products)} results")
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
