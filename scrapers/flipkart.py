import requests, random, time, json, re
from bs4 import BeautifulSoup

HEADERS_LIST = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-IN,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    },
    {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.8",
        "Accept": "text/html,*/*;q=0.8",
        "Connection": "keep-alive",
    },
]


def search_flipkart(query, max_results=12):
    """Scrape Flipkart search results page."""
    time.sleep(random.uniform(0.8, 1.5))
    url = f"https://www.flipkart.com/search?q={requests.utils.quote(query)}&otracker=search&otracker1=search&marketplace=FLIPKART&as-show=on&as=off"
    headers = random.choice(HEADERS_LIST)
    # Add extra headers to mimic a real browser visit
    headers["Referer"] = "https://www.flipkart.com/"
    headers["sec-fetch-site"] = "same-origin"
    headers["sec-fetch-mode"] = "navigate"

    try:
        session = requests.Session()
        # First hit home page to get cookies (helps bypass bot detection)
        session.get("https://www.flipkart.com/", headers=headers, timeout=10)
        time.sleep(random.uniform(0.3, 0.7))
        r = session.get(url, headers=headers, timeout=20)
        r.raise_for_status()
    except Exception as e:
        print(f"[Flipkart] Request failed: {e}")
        return []

    soup = BeautifulSoup(r.text, "lxml")
    products = []

    # Flipkart uses multiple layouts — try each selector pattern
    # Pattern 1: Standard grid product cards (most electronics/general)
    cards = soup.find_all("div", attrs={"data-id": True})

    if not cards:
        # Pattern 2: _1AtVbE / _13oc-S containers
        cards = soup.find_all("div", class_=re.compile(r"_1AtVbE|_2kHMtA|_4ddWXP"))

    if not cards:
        # Pattern 3: product list items
        cards = soup.find_all("div", class_=re.compile(r"_2B099V|_1xHGtK|CXW8mj"))

    for card in cards[:max_results * 2]:  # fetch extra, filter empties later
        if len(products) >= max_results:
            break
        try:
            prod = _parse_card(card)
            if prod:
                products.append(prod)
        except Exception:
            continue

    # Fallback: try JSON embedded in page
    if not products:
        products = _extract_json_products(soup, max_results)

    print(f"[Flipkart] {len(products)} results")
    return products


def _parse_card(card):
    """Extract product info from a single card element."""
    # Title: multiple possible class names Flipkart uses
    title_tag = (
        card.find("div", class_=re.compile(r"_4rR01T|s1Q9rs|IRpwTa|_2WkVRV|wjcEIp")) or
        card.find("a", class_=re.compile(r"s1Q9rs|IRpwTa")) or
        card.find("div", class_="_4rR01T")
    )
    title = title_tag.get_text(strip=True) if title_tag else None
    if not title or len(title) < 4:
        return None

    # Price
    price_tag = (
        card.find("div", class_=re.compile(r"_30jeq3|Nx9bqj|_1_WHN1")) or
        card.find("div", class_="_30jeq3")
    )
    if not price_tag:
        return None
    price = price_tag.get_text(strip=True).replace("₹", "").replace(",", "").strip()
    price = re.sub(r"[^\d.]", "", price)
    if not price:
        return None

    # Image
    img_tag = card.find("img")
    image = ""
    if img_tag:
        image = img_tag.get("src") or img_tag.get("data-src", "")

    # URL
    link_tag = card.find("a", href=True)
    url = ""
    if link_tag:
        href = link_tag["href"]
        url = href if href.startswith("http") else "https://www.flipkart.com" + href

    # Rating
    rating_tag = card.find("div", class_=re.compile(r"_3LWZlK|XQDdHH|gUuXy-"))
    rating = rating_tag.get_text(strip=True) if rating_tag else "N/A"

    return {
        "title": title,
        "price": price,
        "rating": rating,
        "image": image,
        "url": url,
        "source": "Flipkart",
    }


def _extract_json_products(soup, max_results):
    """Try to extract product data from embedded JSON in page scripts."""
    products = []
    for script in soup.find_all("script"):
        txt = script.string or ""
        if '"productUrl"' in txt or '"finalPrice"' in txt:
            try:
                # Find JSON object boundaries
                matches = re.findall(r'\{[^{}]*"productUrl"[^{}]*\}', txt)
                for m in matches[:max_results]:
                    try:
                        obj = json.loads(m)
                        title = obj.get("title") or obj.get("name", "")
                        price = str(obj.get("finalPrice") or obj.get("price", "")).replace(",", "")
                        image = obj.get("imageUrl") or obj.get("image", "")
                        path = obj.get("productUrl") or obj.get("url", "")
                        url = path if path.startswith("http") else "https://www.flipkart.com" + path
                        if title and price:
                            products.append({
                                "title": title, "price": price, "rating": "N/A",
                                "image": image, "url": url, "source": "Flipkart"
                            })
                    except Exception:
                        continue
            except Exception:
                continue
        if products:
            break
    return products
