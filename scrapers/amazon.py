import requests, random, time
from bs4 import BeautifulSoup

HEADERS_LIST = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
     "Accept-Language": "en-IN,en;q=0.9", "Accept-Encoding": "gzip, deflate, br",
     "Accept": "text/html,application/xhtml+xml,*/*;q=0.8", "Connection": "keep-alive"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/123.0.0.0 Safari/537.36",
     "Accept-Language": "en-US,en;q=0.8", "Accept": "text/html,*/*;q=0.8", "Connection": "keep-alive"},
]

def search_amazon(query, max_results=12):
    url = f"https://www.amazon.in/s?k={requests.utils.quote(query)}"
    try:
        time.sleep(random.uniform(0.5, 1.2))
        r = requests.get(url, headers=random.choice(HEADERS_LIST), timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"[Amazon] {e}"); return []
    soup = BeautifulSoup(r.text, "lxml")
    cards = soup.find_all("div", attrs={"data-component-type": "s-search-result"})
    products = []
    for card in cards[:max_results]:
        try:
            t = card.find("h2"); title = t.get_text(strip=True) if t else "N/A"
            pw = card.find("span", class_="a-price-whole")
            if not pw: continue
            price = pw.get_text(strip=True).replace(",","").rstrip(".")
            img = card.find("img", class_="s-image"); image = img["src"] if img else ""
            lnk = card.find("a", class_="a-link-normal", href=True)
            url2 = "https://www.amazon.in" + lnk["href"] if lnk else ""
            rt = card.find("span", class_="a-icon-alt")
            rating = rt.get_text(strip=True).split()[0] if rt else "N/A"
            products.append({"title":title,"price":price,"rating":rating,"image":image,"url":url2,"source":"Amazon"})
        except: continue
    print(f"[Amazon] {len(products)} results"); return products
