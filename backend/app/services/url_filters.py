import re
from urllib.parse import parse_qs, urlparse

from ..schemas import ProductCandidate


GOOD_URL_MARKERS = (
    "/dp/",
    "/gp/product/",
    "/products/",
    "/product/",
    "/listing/",
    "/listings/",
    "/item/",
    "/p/",
    "/shop/p/",
    "/urun/",
    "/urunler/",
)

COLLECTION_URL_MARKERS = (
    "/collections/",
    "/collection/",
    "/market/",
    "/marketplace/",
    "/category/",
    "/categories/",
    "/kategori/",
    "/hediye-setleri/",
)

EDITORIAL_URL_MARKERS = (
    "/gift-guide",
    "/editor",
    "/editors-picks",
    "/curated",
    "/featured",
    "/selections",
    "/secimler",
)

BAD_QUERY_KEYS = {"k", "q", "query", "keyword", "search", "term"}
BAD_PATH_MARKERS = ("/blog", "/blogs", "/news", "/stories", "/story", "/article", "/articles")
BAD_DOMAIN_MARKERS = (
    "instagram.",
    "facebook.",
    "x.com",
    "twitter.",
    "youtube.",
    "tiktok.",
    "pinterest.",
    "reddit.",
    "medium.",
    "blogspot.",
    "wordpress.",
    "vogue.",
    "gq.",
    "wikipedia.",
    "quora.",
    "eksisozluk.",
    "onedio.",
)
SHOPPING_SIGNAL_MARKERS = (
    "sepete",
    "sepet",
    "stok",
    "kargo",
    "fiyat",
    "indirim",
    "ürün",
    "ürünler",
    "mağaza",
    "magaza",
    "shop",
    "store",
    "buy",
    "cart",
    "shopping",
    "collection",
    "kategori",
    "hediye",
    "satın al",
    "online mağaza",
    "online magaza",
    "teslimat",
)
HOST_SHOP_MARKERS = (
    "shop",
    "store",
    "market",
    "boutique",
    "hediye",
    "gift",
)


def _parse_url(raw_url: str):
    try:
        parsed = urlparse(raw_url)
    except Exception:
        return None

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None

    return parsed


def domain_label(raw_url: str) -> str:
    parsed = _parse_url(raw_url)
    if not parsed:
        return ""
    return parsed.netloc.lower().removeprefix("www.")


def source_label_from_url(raw_url: str) -> str:
    domain = domain_label(raw_url)
    if not domain:
        return "Online Mağaza"

    root = domain.split(":", 1)[0]
    if root.endswith(".com.tr"):
        root = root[:-7]
    elif root.endswith(".com"):
        root = root[:-4]
    elif root.endswith(".net"):
        root = root[:-4]
    elif root.endswith(".org"):
        root = root[:-4]
    elif root.endswith(".tr"):
        root = root[:-3]

    main = root.split(".")[-1].replace("-", " ").replace("_", " ").strip()
    if not main:
        return domain

    return " ".join(part.capitalize() for part in main.split())




def _clean_hit_title(title: str) -> str:
    cleaned = " ".join(title.replace("…", "...").split()).strip()
    cleaned = re.sub(r"\s*[:|\-]\s*(amazon|trendyol|hepsiburada|n11|mediamarkt|teknosa|turkcell|shopier|etsy|idefix|kitapyurdu|wraith esports|amazon\.com\.tr).*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"[a-z0-9-]+\.(com|com\.tr|net|org|tr).*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*(kablolu|kablosuz|bluetooth|wireless|rgb|gaming|ultra|shine-through|türkçe q|ingilizce|red switch|blue switch|brown switch|hall effect|tmr hall).*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*,\s*(\d+[.,]?\d*\s*(ghz|mhz|mm|cm|inç|inch|tuşlu|keys?)?|\d+).*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" -:|,")
    while cleaned.endswith((" ...", "...", "..", ".")):
        if cleaned.endswith(" ..."):
            cleaned = cleaned[:-4].rstrip()
        elif cleaned.endswith("..."):
            cleaned = cleaned[:-3].rstrip()
        elif cleaned.endswith(".."):
            cleaned = cleaned[:-2].rstrip()
        else:
            cleaned = cleaned[:-1].rstrip()
    return cleaned[:120].strip(" -:|,")


def tokenize_text(text: str) -> set[str]:
    normalized = "".join(char.lower() if char.isalnum() else " " for char in text)
    return {token for token in normalized.split() if len(token) > 2}


def is_shopping_like_hit(raw_url: str, title: str = "", content: str = "") -> bool:
    parsed = _parse_url(raw_url)
    if not parsed:
        return False

    host = parsed.netloc.lower()
    path = parsed.path.lower().strip()
    query = parse_qs(parsed.query.lower())
    combined = f"{title} {content}".lower()

    if any(marker in host for marker in BAD_DOMAIN_MARKERS):
        return False

    if any(key in BAD_QUERY_KEYS for key in query):
        return False

    if "/search" in path or path == "/s" or path.startswith("/s/"):
        return False

    if any(marker in path for marker in BAD_PATH_MARKERS):
        return False

    if any(marker in path for marker in GOOD_URL_MARKERS + COLLECTION_URL_MARKERS + EDITORIAL_URL_MARKERS):
        return True

    if any(marker in host for marker in HOST_SHOP_MARKERS) and any(marker in combined for marker in SHOPPING_SIGNAL_MARKERS):
        return True

    if any(marker in combined for marker in SHOPPING_SIGNAL_MARKERS):
        return True

    return False


def _classify_url_kind(raw_url: str, title: str = "", content: str = "") -> str | None:
    parsed = _parse_url(raw_url)
    if not parsed:
        return None

    path = parsed.path.lower().strip()
    query = parse_qs(parsed.query.lower())

    if any(key in BAD_QUERY_KEYS for key in query):
        return None

    if path in {"", "/"} or "/search" in path or path == "/s" or path.startswith("/s/"):
        return None

    if not is_shopping_like_hit(raw_url, title, content):
        return None

    if any(marker in path for marker in GOOD_URL_MARKERS):
        return "direct_product"
    if any(marker in path for marker in COLLECTION_URL_MARKERS):
        return "collection"
    if any(marker in path for marker in EDITORIAL_URL_MARKERS):
        return "editorial_pick"
    return "boutique_store"


def is_direct_product_url(raw_url: str) -> bool:
    return _classify_url_kind(raw_url) == "direct_product"


def is_collection_url(raw_url: str) -> bool:
    return _classify_url_kind(raw_url) == "collection"


def is_editorial_pick_url(raw_url: str) -> bool:
    return _classify_url_kind(raw_url) == "editorial_pick"


def is_boutique_store_url(raw_url: str, title: str = "", content: str = "") -> bool:
    return _classify_url_kind(raw_url, title, content) == "boutique_store"


def classify_shopping_hit_kind(raw_url: str, title: str = "", content: str = "") -> str | None:
    return _classify_url_kind(raw_url, title, content)


def score_hit_for_product(product: ProductCandidate, hit: dict) -> int:
    score = 0
    product_tokens = tokenize_text(product.name)
    title_tokens = tokenize_text(str(hit.get("title") or ""))
    content_tokens = tokenize_text(str(hit.get("content") or ""))
    domain = domain_label(str(hit.get("url") or ""))
    source = product.source.lower().strip()

    score += len(product_tokens & title_tokens) * 4
    score += len(product_tokens & content_tokens) * 2

    if source and source in domain:
        score += 3

    if product.name.lower() in str(hit.get("title") or "").lower():
        score += 5

    return score


def _best_hit_for_product(product: ProductCandidate, search_hits: list[dict]) -> tuple[dict | None, int]:
    if not search_hits:
        return None, 0

    ranked_hits = sorted(
        search_hits,
        key=lambda hit: score_hit_for_product(product, hit),
        reverse=True,
    )
    best_hit = ranked_hits[0] if ranked_hits else None
    if not best_hit:
        return None, 0

    return best_hit, score_hit_for_product(product, best_hit)


def _find_hit_by_url(raw_url: str, search_hits: list[dict]) -> dict | None:
    for hit in search_hits:
        if str(hit.get("url") or "") == raw_url:
            return hit
    return None


def _fallback_note(kind: str) -> tuple[str, str]:
    if kind == "collection":
        return (
            "Bağlantı tek bir ürüne değil, seçili benzer seçeneklerin bulunduğu koleksiyon sayfasına açılır.",
            "Bu öneri tekil ürün yerine ilgili seçenekleri bir araya getiren koleksiyon sayfasına yönlendirir.",
        )
    if kind == "boutique_store":
        return (
            "Bağlantı doğrudan ürün yerine ilgili seçeneklerin yer aldığı butik mağaza sayfasına açılır.",
            "Bu öneri tek bir ürün yerine temaya uygun seçenekler sunan butik mağaza sayfasına yönlendirir.",
        )
    return (
        "Bağlantı doğrudan ürün yerine mağazanın editör seçkisi sayfasına açılır.",
        "Bu öneri tekil ürün yerine mağazanın editör seçkisi sayfasına yönlendirir.",
    )


def _normalize_fallback_candidate(product: ProductCandidate, hit: dict, score: int) -> ProductCandidate:
    raw_url = str(product.url)
    if is_direct_product_url(raw_url):
        return product

    hit_title = _clean_hit_title(str(hit.get("title") or "").strip())
    kind = str(hit.get("kind") or "collection")

    if hit_title and score < 8:
        product.name = hit_title

    caveat_text, comparison_text = _fallback_note(kind)
    if caveat_text not in product.caveats:
        product.caveats = [caveat_text, *product.caveats][:2]

    if score < 8:
        product.comparison_note = comparison_text

    return product


def repair_candidate_urls(
    products: list[ProductCandidate], search_hits: list[dict]
) -> list[ProductCandidate]:
    repaired: list[ProductCandidate] = []

    for product in products:
        current_url = str(product.url)
        matched_hit = _find_hit_by_url(current_url, search_hits)
        current_score = score_hit_for_product(product, matched_hit) if matched_hit else 0
        best_hit, best_score = _best_hit_for_product(product, search_hits)

        if (
            best_hit
            and best_score > 0
            and (not matched_hit or (best_score >= current_score + 4 and best_score >= 6))
        ):
            product.url = str(best_hit["url"])
            matched_hit = best_hit
            current_score = best_score
        elif not matched_hit and not classify_shopping_hit_kind(current_url) and best_hit and best_score > 0:
            product.url = str(best_hit["url"])
            matched_hit = best_hit
            current_score = best_score

        if matched_hit:
            if current_score <= 4:
                hit_title = _clean_hit_title(str(matched_hit.get("title") or "").strip())
                if hit_title:
                    product.name = hit_title
            product = _normalize_fallback_candidate(product, matched_hit, current_score)
            product.url = str(matched_hit["url"])
            product.source = source_label_from_url(product.url)

        repaired.append(product)

    return repaired
