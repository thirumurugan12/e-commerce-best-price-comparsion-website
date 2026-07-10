import requests, random, time, json

SEARCH_API = "https://www.myntra.com/gateway/v2/search/{query}?p={page}&rows=24&o=0&plaEnabled=false"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://www.myntra.com/",
    "Origin": "https://www.myntra.com",
    "x-meta-app": "deviceType=desktop",
}

def search_myntra(query, max_results=12):
    time.sleep(random.uniform(0.4, 0.9))
    url = SEARCH_API.format(query=requests.utils.quote(query), page=1)
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"[Myntra] API failed: {e}")
        return _scrape_myntra(query, max_results)

    products_raw = (data.get("products") or
                    data.get("searchData", {}).get("results", {}).get("products") or [])
    products = []
    for item in products_raw[:max_results]:
        try:
            title = (item.get("productDisplayName") or
                     item.get("brandName","") + " " + item.get("name","")).strip()
            price = str(item.get("price") or item.get("priceInfo",{}).get("discountedPrice","")).replace(",","").strip()
            if not price or price == "0": continue
            image = item.get("searchImage") or item.get("imagesURL","")
            pid = item.get("productId") or item.get("id","")
            url2 = f"https://www.myntra.com/{pid}" if pid else "https://www.myntra.com"
            rating = str(item.get("rating") or item.get("ratingCount","N/A"))
            products.append({"title":title,"price":price,"rating":rating,"image":image,"url":url2,"source":"Myntra"})
        except: continue
    print(f"[Myntra] {len(products)} results (API)")
    if not products:
        return _scrape_myntra(query, max_results)
    return products


def _scrape_myntra(query, max_results=12):
    """Fallback: scrape Myntra search page HTML."""
    from bs4 import BeautifulSoup
    url = f"https://www.myntra.com/{requests.utils.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
        "Accept": "text/html,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9",
    }
    try:
        r = requests.get(url, headers=headers, timeout=15); r.raise_for_status()
    except Exception as e:
        print(f"[Myntra fallback] {e}"); return []

    soup = BeautifulSoup(r.text, "lxml")
    # Myntra injects product data as JSON in a script tag
    for script in soup.find_all("script"):
        txt = script.string or ""
        if "pdpData" in txt or "searchData" in txt:
            try:
                start = txt.find("{")
                data = json.loads(txt[start:])
                items = _deep_find(data, "products") or []
                if items: break
            except: continue
    else:
        items = []

    products = []
    for item in items[:max_results]:
        try:
            title = item.get("productDisplayName") or item.get("name","N/A")
            price = str(item.get("price") or 0).replace(",","").strip()
            if not price or price == "0": continue
            image = item.get("searchImage","")
            pid = item.get("productId","")
            url2 = f"https://www.myntra.com/{pid}" if pid else "https://www.myntra.com"
            products.append({"title":title,"price":price,"rating":"N/A","image":image,"url":url2,"source":"Myntra"})
        except: continue
    print(f"[Myntra fallback] {len(products)} results")
    return products


def _deep_find(obj, key):
    if isinstance(obj, dict):
        if key in obj and isinstance(obj[key], list) and obj[key]: return obj[key]
        for v in obj.values():
            r = _deep_find(v, key)
            if r: return r
    elif isinstance(obj, list):
        for i in obj:
            r = _deep_find(i, key)
            if r: return r
    return None
