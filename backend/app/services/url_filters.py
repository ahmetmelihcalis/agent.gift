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
)

BAD_URL_MARKERS = (
    "/search",
    "/s",
    "/market/",
    "/marketplace/",
    "/collections/",
    "/collection/",
    "/category/",
    "/categories/",
    "/gift-guide",
    "/gifts",
    "/tag/",
)

BAD_QUERY_KEYS = {"k", "q", "query", "keyword", "search", "term"}
FALLBACK_URL_MARKERS = (
    "/collections/",
    "/collection/",
    "/market/",
    "/marketplace/",
    "/gift-guide",
    "/gifts",
    "/hediye",
    "/urunler/",
)


def is_direct_product_url(raw_url: str) -> bool:
    try:
        parsed = urlparse(raw_url)
    except Exception:
        return False

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False

    path = parsed.path.lower().strip()
    query = parse_qs(parsed.query.lower())

    if any(marker in path for marker in GOOD_URL_MARKERS):
        return True

    if any(marker in path for marker in BAD_URL_MARKERS):
        return False

    if any(key in BAD_QUERY_KEYS for key in query):
        return False

    if path in {"", "/"}:
        return False

    return True


def is_fallback_collection_url(raw_url: str) -> bool:
    try:
        parsed = urlparse(raw_url)
    except Exception:
        return False

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False

    path = parsed.path.lower().strip()
    query = parse_qs(parsed.query.lower())

    if path in {"", "/"}:
        return False

    if any(key in BAD_QUERY_KEYS for key in query):
        return False

    if "/search" in path or path == "/s" or path.startswith("/s/"):
        return False

    if is_direct_product_url(raw_url):
        return False

    return any(marker in path for marker in FALLBACK_URL_MARKERS)


def is_browseable_result_url(raw_url: str) -> bool:
    try:
        parsed = urlparse(raw_url)
    except Exception:
        return False

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False

    path = parsed.path.lower().strip()
    query = parse_qs(parsed.query.lower())

    if path in {"", "/"}:
        return False

    if any(key in BAD_QUERY_KEYS for key in query):
        return False

    if "/search" in path or path == "/s" or path.startswith("/s/"):
        return False

    return True


def domain_label(raw_url: str) -> str:
    try:
        host = urlparse(raw_url).netloc.lower()
    except Exception:
        return ""

    host = host.removeprefix("www.")
    return host


def tokenize_text(text: str) -> set[str]:
    normalized = "".join(char.lower() if char.isalnum() else " " for char in text)
    return {token for token in normalized.split() if len(token) > 2}


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


def _normalize_fallback_candidate(product: ProductCandidate, hit: dict, score: int) -> ProductCandidate:
    raw_url = str(product.url)
    if is_direct_product_url(raw_url):
        return product

    hit_title = str(hit.get("title") or "").strip()
    if hit_title and score < 8:
        product.name = hit_title

    collection_note = "Bağlantı tek bir ürüne değil, seçili benzer seçeneklerin bulunduğu sayfaya açılır."
    if collection_note not in product.caveats:
        product.caveats = [collection_note, *product.caveats][:2]

    if score < 8:
        product.comparison_note = "Bu öneri tekil ürün yerine ilgili seçenekleri bir araya getiren daha geniş bir sayfaya yönlendirir."

    return product


def repair_candidate_urls(
    products: list[ProductCandidate], search_hits: list[dict]
) -> list[ProductCandidate]:
    repaired: list[ProductCandidate] = []

    for product in products:
        current_url = str(product.url)
        matched_hit = _find_hit_by_url(current_url, search_hits)

        if not matched_hit and not (
            is_direct_product_url(current_url) or is_fallback_collection_url(current_url)
        ):
            best_hit, best_score = _best_hit_for_product(product, search_hits)
            if best_hit and best_score > 0:
                product.url = str(best_hit["url"])
                matched_hit = best_hit

        if matched_hit:
            best_score = score_hit_for_product(product, matched_hit)
            product = _normalize_fallback_candidate(product, matched_hit, best_score)
            product.url = str(matched_hit["url"])

        repaired.append(product)

    return repaired
