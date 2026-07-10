import requests, random, time, json, re
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://www.shopclues.com/",
}


def search_shopclues(query, max_results=12):
    time.sleep(random.uniform(0.4, 0.9))
    url = f"https://www.shopclues.com/search?q={requests.utils.quote(query)}&sort=P_brand&order=desc"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"[ShopClues] {e}")
        return []

    soup = BeautifulSoup(r.text, "lxml")
    products = []

    # ShopClues product cards — class names: "column col3" or "search_blocks"
    cards = (
        soup.find_all("div", class_=re.compile(r"search_blocks|column\s+col3|product_listing", re.I)) or
        soup.find_all("li", class_=re.compile(r"product", re.I))
    )

    for card in cards[:max_results * 2]:
        if len(products) >= max_results:
            break
        try:
            # Title
            t = (
                card.find("p", class_="product_title") or
                card.find("div", class_=re.compile(r"product.?name|pname|title", re.I)) or
                card.find("a", title=True)
            )
            title = (t.get("title") or t.get_text(strip=True)) if t else None
            if not title or len(title) < 4:
                continue

            # Price
            p = (
                card.find("span", class_=re.compile(r"f_price|price|prc", re.I)) or
                card.find("div", class_=re.compile(r"price", re.I))
            )
            if not p:
                continue
            price = re.sub(r"[^\d.]", "", p.get_text(strip=True).replace(",", ""))
            if not price or price == "0":
                continue

            # Image
            img = card.find("img")
            image = ""
            if img:
                image = img.get("data-src") or img.get("src") or img.get("data-original", "")

            # URL
            lnk = card.find("a", href=True)
            href = lnk["href"] if lnk else ""
            url2 = href if href.startswith("http") else "https://www.shopclues.com" + href

            # Rating
            rt = card.find(class_=re.compile(r"rating|stars", re.I))
            rating = rt.get_text(strip=True).split()[0] if rt else "N/A"

            products.append({
                "title": title, "price": price, "rating": rating,
                "image": image, "url": url2, "source": "ShopClues"
            })
        except Exception:
            continue

    print(f"[ShopClues] {len(products)} results")
    return products
