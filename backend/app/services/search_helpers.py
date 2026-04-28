import json

from ..schemas import InvestigateRequest, ProductCandidate, PsychologicalProfile
from .url_filters import (
    is_browseable_result_url,
    is_direct_product_url,
    is_fallback_collection_url,
)


def flatten_search_hits(
    search_results: list[dict],
    allow_fallback: bool = False,
    allow_browseable: bool = False,
) -> list[dict]:
    hits: list[dict] = []
    seen_urls: set[str] = set()

    for group in search_results:
        raw_items = group.get("results") or []
        if isinstance(raw_items, dict):
            raw_items = raw_items.get("results") or raw_items.get("items") or []
        elif isinstance(raw_items, str):
            try:
                parsed_items = json.loads(raw_items)
            except json.JSONDecodeError:
                parsed_items = []
            if isinstance(parsed_items, dict):
                raw_items = parsed_items.get("results") or parsed_items.get("items") or []
            elif isinstance(parsed_items, list):
                raw_items = parsed_items
            else:
                raw_items = []

        if not isinstance(raw_items, list):
            continue

        for item in raw_items:
            if not isinstance(item, dict):
                continue

            url = str(item.get("url") or "").strip()
            title = str(item.get("title") or "").strip()
            content = str(item.get("content") or item.get("snippet") or "").strip()

            is_allowed = is_direct_product_url(url)
            if not is_allowed and allow_fallback:
                is_allowed = is_fallback_collection_url(url)
            if not is_allowed and allow_browseable:
                is_allowed = is_browseable_result_url(url)

            if not url or url in seen_urls or not is_allowed:
                continue

            seen_urls.add(url)
            hits.append(
                {
                    "id": len(hits) + 1,
                    "url": url,
                    "title": title,
                    "content": content[:500],
                }
            )

    return hits


def build_search_queries(
    payload: InvestigateRequest, profile: PsychologicalProfile
) -> list[str]:
    base = payload.brief.strip()
    obsession = profile.obsessions[0] if profile.obsessions else base
    hidden_hook = profile.hidden_hooks[0] if profile.hidden_hooks else base
    aversion = profile.aversions[0] if profile.aversions else ""

    queries = [
        f"{obsession} özgün hediye ürün satın al",
        f"{hidden_hook} koleksiyonluk hediye ürün",
        f"{base} kişiye özel niş hediye ürün",
        f"{base} tasarım hediye ürün butik mağaza",
    ]

    if aversion:
        queries.append(f"{base} klişe olmayan hediye ürün {aversion} olmasın")

    queries.append(f"{base} gift idea product shop")

    deduped: list[str] = []
    seen: set[str] = set()
    for query in queries:
        normalized = query.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            deduped.append(query.strip())

    return deduped


def filter_candidates_against_search_hits(
    products: list[ProductCandidate], allowed_urls: set[str]
) -> list[ProductCandidate]:
    return [product for product in products if str(product.url) in allowed_urls]
