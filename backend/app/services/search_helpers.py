import json

from ..schemas import InvestigateRequest, ProductCandidate, PsychologicalProfile
from .url_filters import classify_shopping_hit_kind


def flatten_search_hits(
    search_results: list[dict],
    allowed_kinds: tuple[str, ...],
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

            kind = classify_shopping_hit_kind(url, title, content)
            if not url or url in seen_urls or kind not in allowed_kinds:
                continue

            seen_urls.add(url)
            hits.append(
                {
                    "id": len(hits) + 1,
                    "url": url,
                    "title": title,
                    "content": content[:500],
                    "kind": kind,
                }
            )

    return hits


def _budget_terms(budget: str | None) -> tuple[str, str]:
    normalized = (budget or "").strip().lower()
    if not normalized:
        return "", ""

    if "0-1000" in normalized or "1000 tl" in normalized and "3000" not in normalized:
        return "0-1000 TL bütçe", "uygun fiyatlı"
    if "1000-3000" in normalized:
        return "1000-3000 TL bütçe", "orta segment"
    if "3000+" in normalized or "3000" in normalized:
        return "3000 TL üzeri bütçe", "üst segment"

    return budget.strip(), ""


def _region_terms(region: str | None) -> tuple[str, str, str]:
    normalized = (region or "Türkiye").strip().lower()
    if "global" in normalized:
        return (
            "global online store",
            "international shipping",
            "shopping site",
        )

    return (
        "Türkiye online alışveriş sitesi",
        "site:.tr",
        "TL fiyat",
    )


def build_search_queries(
    payload: InvestigateRequest, profile: PsychologicalProfile
) -> list[str]:
    base = payload.brief.strip()
    obsession = profile.obsessions[0] if profile.obsessions else base
    hidden_hook = profile.hidden_hooks[0] if profile.hidden_hooks else base
    aversion = profile.aversions[0] if profile.aversions else ""
    budget_primary, budget_style = _budget_terms(payload.budget)
    region_market, region_hint, region_price = _region_terms(payload.region)

    clauses = " ".join(part for part in [budget_primary, budget_style, region_market, region_hint, region_price] if part)

    queries = [
        f"{obsession} hediye ürün satın al {clauses} e ticaret",
        f"{hidden_hook} butik mağaza hediye ürün {clauses}",
        f"{base} koleksiyon hediye ürün {clauses} online mağaza",
        f"{base} mağaza editör seçkisi hediye {clauses}",
        f"{base} özgün hediye ürün {clauses} online store",
        f"{base} gift product shop {budget_primary} {region_market} {region_hint}".strip(),
    ]

    if aversion:
        queries.append(
            f"{base} klişe olmayan hediye ürün {budget_primary} {region_market} {aversion} olmasın"
        )

    deduped: list[str] = []
    seen: set[str] = set()
    for query in queries:
        normalized = " ".join(query.strip().lower().split())
        if normalized and normalized not in seen:
            seen.add(normalized)
            deduped.append(query.strip())

    return deduped


def filter_candidates_against_search_hits(
    products: list[ProductCandidate], allowed_urls: set[str]
) -> list[ProductCandidate]:
    return [product for product in products if str(product.url) in allowed_urls]
