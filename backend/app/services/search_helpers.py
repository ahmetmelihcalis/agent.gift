import re
import json

from ..schemas import InvestigateRequest, ProductCandidate, PsychologicalProfile
from .url_filters import classify_shopping_hit_kind, source_label_from_url, tokenize_text


def _clean_product_title(title: str) -> str:
    cleaned = " ".join(title.replace("…", "...").split()).strip()
    cleaned = re.sub(r"\s*[:|\-]\s*(amazon|trendyol|hepsiburada|n11|mediamarkt|teknosa|turkcell|shopier|etsy|idefix|kitapyurdu|wraith esports|amazon\.com\.tr).*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"[a-z0-9-]+\.(com|com\.tr|net|org|tr).*$", "", cleaned, flags=re.IGNORECASE)
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
    return cleaned[:140].strip()


def _persona_query_hints(text: str) -> list[str]:
    lowered = text.lower()
    hints: list[str] = []

    if any(term in lowered for term in ["yazılım", "software", "developer", "mühendis", "engineer", "kod", "kodlama"]):
        hints.extend([
            "mekanik klavye aksesuarı",
            "masaüstü üretkenlik aksesuarı",
            "tech desk setup ürünü",
            "koleksiyonluk teknoloji objesi",
        ])

    if any(term in lowered for term in ["formula 1", "f1", "otomobil", "araba", "motorsport", "yarış"]):
        hints.extend([
            "motorspor temalı masaüstü obje",
            "formula 1 koleksiyon ürünü",
            "otomobil tutkunu için butik ürün",
        ])

    if any(term in lowered for term in ["doktor", "hekim", "cerrah", "tıp", "medical"]):
        hints.extend([
            "medikal temalı şık masaüstü obje",
            "doktor için işlevsel butik hediye",
        ])

    deduped: list[str] = []
    seen: set[str] = set()
    for hint in hints:
        key = hint.lower().strip()
        if key and key not in seen:
            seen.add(key)
            deduped.append(hint)
    return deduped


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




def build_search_queries(
    payload: InvestigateRequest, profile: PsychologicalProfile
) -> list[str]:
    base = payload.brief.strip()
    obsession = profile.obsessions[0] if profile.obsessions else base
    hidden_hook = profile.hidden_hooks[0] if profile.hidden_hooks else base
    aversion = profile.aversions[0] if profile.aversions else ""
    region_market, region_hint, region_price = ("Türkiye online alışveriş sitesi", "site:.tr", "TL fiyat")

    clauses = " ".join(part for part in [region_market, region_hint, region_price] if part)

    persona_hints = _persona_query_hints(base + " " + obsession + " " + hidden_hook)

    queries = [
        f"{obsession} hediye ürün satın al {clauses} e ticaret",
        f"{hidden_hook} butik mağaza hediye ürün {clauses}",
        f"{base} koleksiyon hediye ürün {clauses} online mağaza",
        f"{base} mağaza editör seçkisi hediye {clauses}",
        f"{base} özgün hediye ürün {clauses} online store",
        f"{base} gift product shop {region_market} {region_hint}".strip(),
    ]

    for hint in persona_hints:
        queries.append(f"{hint} {clauses} alışveriş sitesi")

    if aversion:
        queries.append(
            f"{base} klişe olmayan hediye ürün {region_market} {aversion} olmasın"
        )

    deduped: list[str] = []
    seen: set[str] = set()
    for query in queries:
        normalized = " ".join(query.strip().lower().split())
        if normalized and normalized not in seen:
            seen.add(normalized)
            deduped.append(query.strip())

    return deduped




def build_fallback_candidates(
    search_hits: list[dict], payload: InvestigateRequest, profile: PsychologicalProfile, limit: int = 5
) -> list[ProductCandidate]:
    fallback: list[ProductCandidate] = []
    signals = [*profile.obsessions[:2], *profile.hidden_hooks[:1]]
    persona_hint = (profile.obsessions[:1] or profile.hidden_hooks[:1] or [profile.inferred_persona or payload.brief[:80]])[0]

    for hit in search_hits:
        title = _clean_product_title(str(hit.get("title") or "").strip())
        url = str(hit.get("url") or "").strip()
        if not title or not url:
            continue

        source = source_label_from_url(url)
        kind = str(hit.get("kind") or "collection")
        caveats: list[str] = []
        if kind != "direct_product":
            caveats.append("Bu bağlantı tekil ürün yerine benzer seçeneklerin bulunduğu bir sayfaya açılabilir.")

        fallback.append(
            ProductCandidate(
                name=title,
                why_it_matches=f"{persona_hint} tarafına yakın duran daha güvenli bir seçenek.",
                price_label="Fiyat bilgisi değişken",
                url=url,
                source=source,
                editorial_note="Arama sonuçlarından seçilen yakın eşleşme.",
                matched_signals=signals[:3],
                caveats=caveats,
                comparison_note="Doğrudan eşleşme zayıf kaldığında güvenli fallback olarak öne çıktı.",
            )
        )

        if len(fallback) >= limit:
            break

    return fallback




def _candidate_relevance_score(product: ProductCandidate, payload: InvestigateRequest, profile: PsychologicalProfile) -> int:
    context = " ".join([
        payload.brief,
        profile.inferred_persona,
        " ".join(profile.obsessions),
        " ".join(profile.hidden_hooks),
        " ".join(profile.aversions),
    ])
    context_tokens = tokenize_text(context)
    product_text = " ".join([
        product.name,
        product.why_it_matches,
        product.editorial_note,
        " ".join(product.matched_signals),
    ])
    product_tokens = tokenize_text(product_text)

    score = len(context_tokens & product_tokens) * 2

    lowered_name = product.name.lower()
    generic_markers = (
        "koleksiyon", "seçki", "secim", "ürün seçkisi", "platformu", "kategori", "mağaza", "magaza", "seti"
    )
    if any(marker in lowered_name for marker in generic_markers):
        score -= 2

    role_text = payload.brief.lower()
    if any(term in role_text for term in ["yazılım", "developer", "software", "kod", "mühendis"]):
        preferred = ("klavye", "keyboard", "desk", "masa", "switch", "teknoloji", "aksesuar", "monitor", "stand", "dock")
        discouraged = ("bardak", "kupa", "tabak", "mutfak", "termos", "vazo", "mum")
        if any(marker in lowered_name for marker in preferred):
            score += 4
        if any(marker in lowered_name for marker in discouraged):
            score -= 6

    kind = classify_shopping_hit_kind(str(product.url), product.name, product.why_it_matches)
    if kind == 'direct_product':
        score += 3
    elif kind == 'collection':
        score -= 1
    elif kind in {'boutique_store', 'editorial_pick'}:
        score += 0

    return score


def rank_candidates_for_profile(products: list[ProductCandidate], payload: InvestigateRequest, profile: PsychologicalProfile) -> list[ProductCandidate]:
    return sorted(products, key=lambda product: _candidate_relevance_score(product, payload, profile), reverse=True)


def filter_candidates_against_search_hits(
    products: list[ProductCandidate], allowed_urls: set[str]
) -> list[ProductCandidate]:
    return [product for product in products if str(product.url) in allowed_urls]
