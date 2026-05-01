import re
import json

from ..schemas import InvestigateRequest, ProductCandidate, PsychologicalProfile

from .url_filters import classify_shopping_hit_kind, source_label_from_url, tokenize_text


def _dedupe_phrases(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = " ".join(str(value or "").split()).strip()
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            deduped.append(cleaned)
    return deduped


def _profile_signal_phrases(payload: InvestigateRequest, profile: PsychologicalProfile) -> list[str]:
    return _dedupe_phrases([
        *profile.product_affinities,
        *profile.use_contexts,
        *profile.obsessions,
        *profile.hidden_hooks,
        profile.inferred_persona,
        payload.brief,
    ])


def _profile_avoidance_phrases(profile: PsychologicalProfile) -> list[str]:
    return _dedupe_phrases([
        *profile.product_avoidances,
        *profile.aversions,
        *profile.gifting_risks,
    ])


def _signal_phrase_score(phrases: list[str], product_text: str, product_tokens: set[str], weight: int = 2) -> int:
    score = 0
    lowered_text = product_text.lower()
    for phrase in phrases[:10]:
        lowered_phrase = phrase.lower()
        phrase_tokens = tokenize_text(phrase)
        if lowered_phrase and lowered_phrase in lowered_text:
            score += max(weight + 1, len(phrase_tokens))
            continue
        overlap = len(phrase_tokens & product_tokens)
        if overlap >= 2:
            score += weight + overlap
        elif overlap == 1:
            score += 1
    return score


def _clean_product_title(title: str) -> str:
    cleaned = " ".join(title.replace("…", "...").split()).strip()
    cleaned = re.sub(r"\s*[:|\-]\s*(amazon|trendyol|hepsiburada|n11|mediamarkt|teknosa|turkcell|shopier|etsy|idefix|kitapyurdu|wraith esports|welcomebaby|bitmeyenkartus|koçtaş|koctas|amazon\.com\.tr).*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b[a-z0-9-]+\.(com|com\.tr|net|org|tr)\b.*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*[|:]\s*[^|:]*$", "", cleaned)
    cleaned = re.sub(r"\s*[\-–—]\s*(en uygun fiyat(larla)?|sat[ıi]n al[ıi]n?[^-–—|:]*|fiyat[ıi]? ve özellikleri.*|özellikleri.*|kampanya.*|indirim.*)$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(en uygun fiyat(larla)?|sat[ıi]n al[ıi]n?|fiyat[ıi]? ve özellikleri|özellikleri|kampanya|indirim)\b.*$", "", cleaned, flags=re.IGNORECASE)
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


_PERSONA_HINT_RULES: list[tuple[tuple[str, ...], tuple[str, ...]]] = [
    (("yazılım", "software", "developer", "mühendis", "engineer", "kod", "kodlama"), (
        "mekanik klavye aksesuarı",
        "masaüstü üretkenlik aksesuarı",
        "tech desk setup ürünü",
    )),
    (("formula 1", "f1", "otomobil", "araba", "motorsport", "yarış"), (
        "motorspor temalı masaüstü obje",
        "formula 1 koleksiyon ürünü",
        "otomobil tutkunu için teknik hediye",
    )),
    (("öğretmen", "teacher", "öğretmenlik", "sınıf", "classroom"), (
        "öğretmen için masaüstü düzen ürünü",
        "eğitim odaklı şık kırtasiye",
        "sınıf dışında günlük kullanım hediyesi",
    )),
    (("öğrenci", "student", "üniversite", "college", "campus"), (
        "öğrenci için masaüstü verimlilik ürünü",
        "günlük kullanıma uygun bütçe dostu aksesuar",
        "çalışma masası organizasyon ürünü",
    )),
    (("doktor", "hekim", "cerrah", "tıp", "medical"), (
        "doktor için işlevsel butik hediye",
        "masaüstü kullanımına uygun şık aksesuar",
        "yoğun tempoya uygun pratik ürün",
    )),
    (("mimar", "architect", "iç mimar", "industrial designer", "tasarımcı", "designer", "grafik"), (
        "tasarım odaklı masaüstü obje",
        "estetik ve işlevsel ofis aksesuarı",
        "yaratıcı profesyonel için butik ürün",
    )),
    (("oyun", "gamer", "gaming", "esports", "steam", "konsol"), (
        "oyuncu masaüstü aksesuarı",
        "gaming setup ürünü",
        "esports temalı kullanışlı hediye",
    )),
    (("fotoğraf", "photography", "kamera", "camera", "içerik üretici", "content creator", "video"), (
        "fotoğrafçı için masaüstü ekipmanı",
        "içerik üreticisi aksesuarı",
        "kamera düzenleme ürünü",
    )),
    (("kitap", "reader", "roman", "edebiyat", "literature", "okumayı"), (
        "kitap sever için okuma aksesuarı",
        "edebiyat temalı butik hediye",
        "kitaplık yanında kullanılabilecek obje",
    )),
    (("kahve", "coffee", "çay", "tea", "barista"), (
        "kahve ritüeline eşlik eden aksesuar",
        "çalışma molalarına uygun şık ürün",
        "kahve sever için butik masaüstü ürünü",
    )),
    (("müzik", "music", "gitar", "piyano", "vinyl", "plak", "kulaklık"), (
        "müzik tutkunu için masaüstü aksesuar",
        "ses ekipmanı odaklı ürün",
        "müzik temalı butik obje",
    )),
    (("spor", "fitness", "gym", "koşu", "run", "pilates", "yoga"), (
        "aktif yaşam tarzına uygun günlük ürün",
        "spor sonrası kullanım aksesuarı",
        "fitness odaklı işlevsel hediye",
    )),
    (("seyahat", "travel", "gezgin", "trip", "tatil", "valiz"), (
        "seyahat dostu organizasyon ürünü",
        "gezgin için kompakt aksesuar",
        "günlük taşımaya uygun pratik hediye",
    )),
    (("bebek", "anne", "mother", "newborn", "baby", "ebeveyn", "parent"), (
        "ebeveyn için günlük kullanım ürünü",
        "bebekli yaşamı kolaylaştıran butik ürün",
        "anne için işlevsel hediye",
    )),
    (("kedi", "köpek", "pet", "evcil hayvan"), (
        "evcil hayvan sever için günlük aksesuar",
        "pet temalı butik hediye",
        "evcil hayvan yaşamına uygun kullanışlı ürün",
    )),
    (("minimal", "minimalist", "sade", "clean", "düzenli"), (
        "minimal tasarımlı masaüstü aksesuar",
        "sade ama işlevsel hediye",
        "temiz çizgili dekoratif olmayan ürün",
    )),
    (("koleksiyon", "collector", "biriktir", "limited edition", "özel seri"), (
        "koleksiyonluk butik ürün",
        "özel seri hediye",
        "sergilenebilir karakterli obje",
    )),
    (("avukat", "lawyer", "hukuk", "legal", "mahkeme", "dava"), (
        "avukat için masaüstü organizasyon ürünü",
        "hukuk profesyoneline uygun şık aksesuar",
        "resmi ama karakterli günlük kullanım hediyesi",
    )),
    (("psikolog", "psychologist", "terapist", "therapy", "counselor"), (
        "psikolog için sakin ve işlevsel masaüstü ürünü",
        "danışma odasına uygun sade aksesuar",
        "günlük kullanımda rahatlık sunan butik ürün",
    )),
    (("girişimci", "entrepreneur", "startup", "kurucu", "founder"), (
        "girişimci için masaüstü verimlilik ürünü",
        "yoğun tempoya uygun pratik aksesuar",
        "çalışma akışını hızlandıran işlevsel hediye",
    )),
    (("akademisyen", "academic", "araştırmacı", "researcher", "profesör", "lecturer"), (
        "akademisyen için çalışma masası aksesuarı",
        "araştırma odaklı günlük kullanım ürünü",
        "okuma ve not alma rutinine uygun hediye",
    )),
    (("kamp", "camping", "doğa", "outdoor", "trekking", "karavan"), (
        "kampçı için taşınabilir aksesuar",
        "outdoor kullanımına uygun pratik ürün",
        "doğa odaklı işlevsel hediye",
    )),
    (("maker", "arduino", "robotik", "3d printer", "3d yazıcı", "otomasyon", "diy"), (
        "maker masaüstü ekipmanı",
        "elektronik proje aksesuarı",
        "robotik ve otomasyon odaklı butik ürün",
    )),
]


def _persona_query_hints(payload: InvestigateRequest, profile: PsychologicalProfile) -> list[str]:
    signal_hints = [
        *profile.product_affinities[:4],
        *profile.use_contexts[:3],
        *profile.hidden_hooks[:2],
    ]

    fallback_hints: list[str] = []
    lowered = (payload.brief + " " + profile.inferred_persona).lower()
    for triggers, hints in _PERSONA_HINT_RULES:
        if any(term in lowered for term in triggers):
            fallback_hints.extend(hints)

    return _dedupe_phrases([*signal_hints, *fallback_hints])


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

    persona_hints = _persona_query_hints(payload, profile)

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
        " ".join(profile.product_affinities),
        " ".join(profile.use_contexts),
    ])
    context_tokens = tokenize_text(context)
    product_text = " ".join([
        product.name,
        product.why_it_matches,
        product.editorial_note,
        " ".join(product.matched_signals),
        product.comparison_note,
    ])
    product_tokens = tokenize_text(product_text)

    score = len(context_tokens & product_tokens) * 2
    score += _signal_phrase_score(_profile_signal_phrases(payload, profile), product_text, product_tokens, weight=4)
    score -= _signal_phrase_score(_profile_avoidance_phrases(profile), product_text, product_tokens, weight=2)

    lowered_name = product.name.lower()
    lowered_text = product_text.lower()
    generic_markers = (
        "koleksiyon", "seçki", "secim", "ürün seçkisi", "platformu", "kategori", "mağaza", "magaza", "seti"
    )
    if any(marker in lowered_name for marker in generic_markers):
        score -= 2

    generic_office_markers = (
        "mobilya", "koltuk", "dolap", "raf", "çalışma masası", "ofis mobilya", "network kablo", "bağlantı kablosu"
    )
    if any(marker in lowered_name or marker in lowered_text for marker in generic_office_markers):
        score -= 3

    role_text = payload.brief.lower()
    if any(term in role_text for term in ["yazılım", "developer", "software", "kod", "mühendis"]):
        preferred = (
            "klavye", "keyboard", "desk", "switch", "teknoloji", "aksesuar", "monitor", "stand", "dock",
            "wrist rest", "bilek", "desk mat", "mousepad", "hub", "usb", "cable management", "kablo yönetim"
        )
        discouraged = ("bardak", "kupa", "tabak", "mutfak", "termos", "vazo", "mum")
        if any(marker in lowered_name for marker in preferred):
            score += 4
        if any(marker in lowered_name for marker in discouraged):
            score -= 5

    if any(term in role_text for term in ["formula 1", "f1", "otomobil", "motorspor", "yarış", "mclaren", "ferrari"]):
        motorsport_preferred = ("formula", "f1", "motorspor", "yarış", "sim", "lego", "model", "kitap", "telemetry", "engineering")
        if any(marker in lowered_name or marker in lowered_text for marker in motorsport_preferred):
            score += 3

    kind = classify_shopping_hit_kind(str(product.url), product.name, product.why_it_matches)
    if kind == 'direct_product':
        score += 3
    elif kind == 'collection':
        score -= 1

    return score


def rank_candidates_for_profile(products: list[ProductCandidate], payload: InvestigateRequest, profile: PsychologicalProfile) -> list[ProductCandidate]:
    return sorted(products, key=lambda product: _candidate_relevance_score(product, payload, profile), reverse=True)


def filter_candidates_against_search_hits(
    products: list[ProductCandidate], allowed_urls: set[str]
) -> list[ProductCandidate]:
    return [product for product in products if str(product.url) in allowed_urls]
