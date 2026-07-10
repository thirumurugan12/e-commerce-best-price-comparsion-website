import concurrent.futures
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import SearchHistory
from scrapers import search_amazon, search_snapdeal, search_jiomart, search_ajio, search_tatacliq, search_shopclues

SITE_NAME = "BestPrice"

CATEGORIES = [
    {"name": "Premium Smartphones", "query": "premium smartphone",      "price": "₹34,999", "label": "Starting from", "emoji": "📱"},
    {"name": "Mid-Range 5G Phones",  "query": "5g smartphone",          "price": "₹14,999", "label": "Under",         "emoji": "📲"},
    {"name": "Budget Laptops",       "query": "budget laptop",          "price": "₹34,999", "label": "Under",         "emoji": "💻"},
    {"name": "Smart Televisions",    "query": "smart tv 32 inch",       "price": "₹6,999",  "label": "Under",         "emoji": "📺"},
    {"name": "Refrigerators",        "query": "refrigerator double door","price":"₹14,999", "label": "Under",         "emoji": "🧊"},
    {"name": "Washing Machines",     "query": "washing machine fully automatic","price":"₹16,999","label":"Under",    "emoji": "🫧"},
    {"name": "Headphones",           "query": "wireless headphones",    "price": "₹999",    "label": "Under",         "emoji": "🎧"},
    {"name": "Smartwatches",         "query": "smartwatch",             "price": "₹1,999",  "label": "Under",         "emoji": "⌚"},
    {"name": "Cameras",              "query": "digital camera",         "price": "₹24,999", "label": "Under",         "emoji": "📷"},
]

HOT_DEALS  = [99, 199, 299, 399, 499, 599, 799, 999]
DISCOUNTS  = [40, 50, 60, 70]
ALL_STORES = ["Amazon", "Snapdeal", "JioMart", "AJIO", "TataCLiQ", "ShopClues"]


def _safe_recent():
    """Return recent searches — never crashes even if DB table missing."""
    try:
        return list(SearchHistory.objects.values_list('query', flat=True)[:8])
    except Exception:
        return []


def _to_float(p):
    try:
        return float(str(p).replace(",", "").replace("₹", "").strip())
    except Exception:
        return float("inf")


def home(request):
    return render(request, "store/home.html", {
        "site": SITE_NAME,
        "recent": _safe_recent(),
        "categories": CATEGORIES,
        "hot_deals": HOT_DEALS,
        "discounts": DISCOUNTS,
    })


def results(request):
    query     = request.GET.get("q", "").strip()
    sort_by   = request.GET.get("sort", "price_asc")
    min_price = request.GET.get("min_price", "")
    max_price = request.GET.get("max_price", "")
    stores    = request.GET.getlist("store")

    if not query:
        return redirect("/")

    # Save history safely
    try:
        SearchHistory.objects.get_or_create(query=query.lower())
    except Exception:
        pass

    scrapers = {
        "Amazon":    search_amazon,
        "Snapdeal":  search_snapdeal,
        "JioMart":   search_jiomart,
        "AJIO":      search_ajio,
        "TataCLiQ":  search_tatacliq,
        "ShopClues": search_shopclues,
    }

    all_products, scraper_status = [], {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(fn, query, 15): name for name, fn in scrapers.items()}
        for f in concurrent.futures.as_completed(futures):
            name = futures[f]
            try:
                prods = f.result(timeout=20)
                all_products.extend(prods)
                scraper_status[name] = len(prods)
            except Exception as e:
                print(f"[{name}] {e}")
                scraper_status[name] = 0

    # Ensure all stores shown even if 0
    for s in ALL_STORES:
        scraper_status.setdefault(s, 0)

    # Filter by store
    if stores:
        all_products = [p for p in all_products if p["source"] in stores]

    # Filter by price
    if min_price:
        try:
            all_products = [p for p in all_products if _to_float(p["price"]) >= float(min_price)]
        except ValueError: pass
    if max_price:
        try:
            all_products = [p for p in all_products if _to_float(p["price"]) <= float(max_price)]
        except ValueError: pass

    # Sort
    if sort_by == "price_asc":
        all_products.sort(key=lambda p: _to_float(p["price"]))
    elif sort_by == "price_desc":
        all_products.sort(key=lambda p: _to_float(p["price"]), reverse=True)
    elif sort_by == "rating":
        def _r(p):
            try: return -float(str(p.get("rating","0")).split()[0])
            except: return 0
        all_products.sort(key=_r)

    if all_products:
        all_products[0]["cheapest"] = True

    prices = [_to_float(p["price"]) for p in all_products if _to_float(p["price"]) != float("inf")]

    return render(request, "store/results.html", {
        "site":            SITE_NAME,
        "query":           query,
        "products":        all_products,
        "scraper_status":  scraper_status,
        "total":           len(all_products),
        "sort_by":         sort_by,
        "min_price":       min_price,
        "max_price":       max_price,
        "selected_stores": stores,
        "price_min_found": int(min(prices)) if prices else 0,
        "price_max_found": int(max(prices)) if prices else 500000,
        "all_stores":      ALL_STORES,
        "recent":          _safe_recent(),
    })


def login_page(request):
    error = ""
    if request.method == "POST":
        action = request.POST.get("action")
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if action == "register":
            email = request.POST.get("email", "").strip()
            if User.objects.filter(username=username).exists():
                error = "Username already taken. Please choose another."
            elif len(password) < 6:
                error = "Password must be at least 6 characters."
            else:
                User.objects.create_user(username=username, email=email, password=password)
                user = authenticate(request, username=username, password=password)
                login(request, user)
                return redirect("/")
        else:  # login
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect(request.GET.get("next", "/"))
            else:
                error = "Incorrect username or password."

    return render(request, "store/login.html", {"site": SITE_NAME, "error": error})


def logout_view(request):
    logout(request)
    return redirect("/")
