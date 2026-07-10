import requests, random, time
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
           "Accept-Language": "en-IN,en;q=0.9", "Connection": "keep-alive"}

def search_snapdeal(query, max_results=12):
    url = f"https://www.snapdeal.com/search?keyword={requests.utils.quote(query)}&sort=plrty"
    try:
        time.sleep(random.uniform(0.3, 0.8))
        r = requests.get(url, headers=HEADERS, timeout=15); r.raise_for_status()
    except Exception as e:
        print(f"[Snapdeal] {e}"); return []
    soup = BeautifulSoup(r.text, "lxml")
    cards = soup.find_all("div", class_="product-tuple-listing")
    products = []
    for card in cards[:max_results]:
        try:
            t = card.find("p", class_="product-title"); title = t.get_text(strip=True) if t else "N/A"
            p = card.find("span", class_="product-price")
            if not p: continue
            price = p.get_text(strip=True).replace("Rs.","").replace("₹","").replace(",","").strip()
            img = card.find("img"); image = (img.get("src") or img.get("data-src","")) if img else ""
            lnk = card.find("a", class_="dp-widget-link"); pu = lnk["href"] if lnk else ""
            products.append({"title":title,"price":price,"rating":"N/A","image":image,"url":pu,"source":"Snapdeal"})
        except: continue
    print(f"[Snapdeal] {len(products)} results"); return products
