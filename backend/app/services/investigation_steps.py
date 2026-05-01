import asyncio
import json
import uuid

from pydantic import ValidationError

from ..agents import build_chat_llm, build_search_tool
from ..config import Settings
from ..schemas import (
    AgentDescriptor,
    InvestigateRequest,
    InvestigationResult,
    ProductCandidate,
    PsychologicalProfile,
    WorkflowStep,
)
from .agent_state import build_filter_summary
from .curation import diversify_curated_products, fill_missing_curated_products, hydrate_curated_products
from .json_utils import InvestigationError, extract_or_repair_json
from .search_helpers import (
    build_fallback_candidates,
    build_search_queries,
    filter_candidates_against_search_hits,
    flatten_search_hits,
    rank_candidates_for_profile,
)
from .url_filters import repair_candidate_urls


async def rewrite_final_product_explanations(
    payload: InvestigateRequest,
    profile: PsychologicalProfile,
    products: list[dict],
    settings: Settings,
) -> list[dict]:
    if not products:
        return products

    llm = build_chat_llm(settings, temperature=0.2)
    prompt = f"""
Aşağıdaki hediye ürünleri için açıklamaları yeniden yaz.
Yalnızca geçerli JSON dön.

Kurallar:
- Çıktı dili tamamen Türkçe olsun.
- Her ürün için `why_it_matches` alanı en fazla 1 kısa cümle olsun.
- Her ürün için `editorial_note` alanı en fazla 1 kısa cümle olsun.
- Açıklama doğrudan ürün adına sadık kalsın.
- Ürün adı klavye ise kitap, bardak, tabak, kablo, termos gibi başka nesnelerden söz etme.
- Ürün adı kitap ise klavye, araç aksesuarı, LEGO veya alakasız başka bir ürünü anlatma.
- Genel metafor, süslü anlatım ve reklam dili kullanma.
- Kısa, sade, net ve promptla doğrudan ilgili ol.

Kullanıcı girdisi:
{payload.brief}

Psikolojik profil:
{profile.model_dump_json(indent=2)}

Ürünler:
{json.dumps(products, ensure_ascii=False, indent=2)}

JSON şeması:
{{
  "products": [
    {{
      "name": "string",
      "why_it_matches": "string",
      "editorial_note": "string"
    }}
  ]
}}
"""

    try:
        response = await llm.ainvoke(prompt)
        raw_text = response.content if hasattr(response, "content") else str(response)
        rewritten_payload = await extract_or_repair_json(raw_text, settings)
        rewritten_products = rewritten_payload.get("products")
        if not isinstance(rewritten_products, list):
            return products

        rewritten_by_name = {
            str(item.get("name") or "").strip().lower(): item
            for item in rewritten_products
            if isinstance(item, dict) and item.get("name")
        }

        normalized: list[dict] = []
        for product in products:
            key = str(product.get("name") or "").strip().lower()
            rewritten = rewritten_by_name.get(key, {})
            updated = dict(product)
            if isinstance(rewritten.get("why_it_matches"), str) and rewritten.get("why_it_matches", "").strip():
                updated["why_it_matches"] = rewritten["why_it_matches"].strip()
            if isinstance(rewritten.get("editorial_note"), str) and rewritten.get("editorial_note", "").strip():
                updated["editorial_note"] = rewritten["editorial_note"].strip()
            normalized.append(updated)
        return normalized
    except Exception:
        return products


def build_fallback_result_payload(
    request_payload: InvestigateRequest,
    profile: PsychologicalProfile,
    candidates: list[ProductCandidate],
    filters: dict,
    agents: list[AgentDescriptor],
    workflow: list[WorkflowStep],
) -> dict:
    final_products = fill_missing_curated_products([], candidates, 3)[:3]
    profile_summary = profile.inferred_persona or request_payload.brief[:160]
    editorial_intro = (
        "En yakın ürünler, kişinin öne çıkan ilgi alanları ve günlük kullanım ihtimali dikkate alınarak seçildi."
    )
    markdown = "\n".join(
        [
            "### Önerilen Ürünler",
            *[f"- **{item['name']}**: {item['why_it_matches']}" for item in final_products],
        ]
    )
    return {
        "session_id": str(uuid.uuid4()),
        "profile_summary": profile_summary,
        "editorial_intro": editorial_intro,
        "markdown": markdown,
        "tone_mode": filters["tone_mode"],
        "applied_filters": filters,
        "profile_snapshot": profile.model_dump(mode="json"),
        "agents": [agent.model_dump(mode="json") for agent in agents],
        "workflow": [step.model_dump(mode="json") for step in workflow],
        "products": final_products,
    }


async def generate_profile(payload: InvestigateRequest, settings: Settings) -> PsychologicalProfile:
    llm = build_chat_llm(settings, temperature=0.4)
    filters = build_filter_summary(payload)
    prompt = f"""
Sen Psikolojik Profil Uzmanısın.
Kullanıcı girdisini analiz et ve yalnızca geçerli JSON dön.

Kullanıcı girdisi:
{payload.brief}

Bağlam filtreleri:
{json.dumps(filters, ensure_ascii=False, indent=2)}

Kurallar:
- Çıktı dili tamamen Türkçe olsun.
- Doğal, gündelik ve akıcı Türkçe kullan; çeviri kokan ya da fazla yapay duran cümleler kurma.
- Kişinin açıkça söylemediği eğilimleri dikkatle çıkar.
- "obsessions", "aversions" ve "hidden_hooks" alanlarına kısa, net ve kulağa doğal gelen ifadeler yaz.
- Psikolojik analiz tonuna kaçıp ağdalı cümleler kurma; gözlemci ve yerinde kal.

JSON şeması:
{{
  "inferred_persona": "string",
  "obsessions": ["string"],
  "aversions": ["string"],
  "hidden_hooks": ["string"],
  "gifting_risks": ["string"],
  "tone_notes": "string"
}}
"""
    response = await llm.ainvoke(prompt)
    raw_text = response.content if hasattr(response, "content") else str(response)
    profile_payload = await extract_or_repair_json(raw_text, settings)
    try:
        return PsychologicalProfile.model_validate(profile_payload)
    except ValidationError as exc:
        raise InvestigationError("Psikolojik profil beklenen formata uymuyor.") from exc


async def search_candidates(
    payload: InvestigateRequest, profile: PsychologicalProfile, settings: Settings
) -> list[ProductCandidate]:
    search_tool = build_search_tool(settings)
    llm = build_chat_llm(settings, temperature=0.6)
    filters = build_filter_summary(payload)

    queries = build_search_queries(payload, profile)
    search_results: list[dict] = []
    first_pass_queries = queries[:4]
    second_pass_queries = queries[4:6]

    for query in first_pass_queries:
        result = await asyncio.to_thread(search_tool.invoke, query)
        search_results.append({"query": query, "results": result})

    direct_hits = flatten_search_hits(search_results, ("direct_product",))
    if len(direct_hits) < 2 and second_pass_queries:
        for query in second_pass_queries:
            result = await asyncio.to_thread(search_tool.invoke, query)
            search_results.append({"query": query, "results": result})
        direct_hits = flatten_search_hits(search_results, ("direct_product",))

    search_hits = direct_hits
    if len(search_hits) < 2:
        search_hits = flatten_search_hits(search_results, ("direct_product", "collection"))
    if len(search_hits) < 2:
        search_hits = flatten_search_hits(search_results, ("direct_product", "collection", "boutique_store"))
    if len(search_hits) < 2:
        search_hits = flatten_search_hits(search_results, ("direct_product", "collection", "boutique_store", "editorial_pick"))

    if not search_hits:
        raise InvestigationError("Arama sonuçları yeterince güçlü ürün, koleksiyon veya mağaza bağlantısı üretmedi.")

    allowed_urls = {item["url"] for item in search_hits}
    prompt = f"""
Sen Ürün Avcısısın.
Kupa, tişört, jenerik mum, genel hediye kartı, blog yazısı, sosyal medya bağlantısı ve tembel seçimleri reddet.
Aşağıdaki profil ve arama sonuçlarını kullanarak tam 5 adet niş, şaşırtıcı hediye adayı seç.
Yalnızca geçerli JSON dön.

Kurallar:
- Çıktı dili tamamen Türkçe olsun.
- Türkçesi çevrilmiş gibi duran kalıplardan kaçın; doğal ve yaşayan bir dil kullan.
- Ürünler yalnızca internet alışveriş siteleri ve gerçek e-ticaret mağazalarından gelsin.
- Blog, forum, sosyal medya, haber sitesi veya mağaza dışı editoryal içerik sitesi kullanma.
- Mümkün olduğunda doğrudan ürün sayfasını tercih et.
- Doğrudan ürün yoksa sırasıyla koleksiyon sayfası, butik mağaza sayfası ve mağazanın editör seçkisi sayfasını fallback olarak kullanabilirsin.
- Seçtiğin adaylar kullanıcının seçtiği bütçe ve bölge kısıtına mümkün olduğunca uysun.
- Arama filtresi içeren sayfaları kullanma.
- Eğer kullandığın bağlantı tek bir ürüne değil, koleksiyon ya da liste sayfasına açılıyorsa ürün adı uydurma.
- Böyle durumlarda `name` alanı sayfanın gerçekten sunduğu ürün grubunu ya da koleksiyon başlığını yansıtsın.
- `url` alanı, aşağıdaki arama hitlerinden birinin URL'si ile birebir aynı olmak zorunda.
- Eğer yalnızca koleksiyon veya seçili liste sayfası varsa, bunu ancak gerçekten profile uygun ürünleri bir araya getiren güçlü bir kaynak olarak kullan.
- Aynı fikrin varyasyonlarını sıralama.
- Mümkün olduğunda ürünleri farklı mağaza ve kaynaklardan seç; gerekmedikçe aynı siteden birden fazla ürün çıkarma.
- Çok genel zayıf seçimleri ele.
- Kişinin mesleği veya baskın ilgi alanı teknoloji, yazılım, mühendislik ya da üretkenlik odaklıysa; sofra ürünü, kupa, bardak, tabak, dekoratif mutfak eşyası gibi düşük ilişkili ürünleri ancak kullanıcı açıkça istiyorsa düşün.
- Meslek veya hobi sinyali güçlü olduğunda ürünün bununla doğrudan ilişkili olması gerekir.
- Her ürün için neden uygun olduğunu kısa ve sade bir Türkçeyle açıkla.
- `why_it_matches` tam olarak 1 kısa cümle olsun.
- `why_it_matches` alanı doğrudan ürünün kendisine bağlı olsun.
- Ürün ile açıklama arasında kategori kayması olmasın.
- `matched_signals` alanında ürünü eşleştiren 2-4 kısa sinyal yaz.
- `caveats` alanında dikkat edilmesi gereken 0-2 kısa not yaz.
- `comparison_note` alanında ürünü diğerlerinden ayıran tek cümlelik kısa ve doğal bir not ver.

Kullanıcı girdisi:
{payload.brief}

Filtreler:
{json.dumps(filters, ensure_ascii=False, indent=2)}

Psikolojik profil:
{profile.model_dump_json(indent=2)}

Kullanılabilir arama hitleri:
{json.dumps(search_hits, ensure_ascii=False, indent=2)}

JSON şeması:
{{
  "products": [
    {{
      "name": "string",
      "why_it_matches": "string",
      "price_label": "string",
      "url": "https://example.com",
      "source": "string",
      "editorial_note": "string",
      "matched_signals": ["string"],
      "caveats": ["string"],
      "comparison_note": "string"
    }}
  ]
}}
"""

    fallback_candidates = build_fallback_candidates(search_hits, payload, profile, limit=5)
    response_payload: dict = {}
    try:
        response = await llm.ainvoke(prompt)
        raw_text = response.content if hasattr(response, "content") else str(response)
        response_payload = await extract_or_repair_json(raw_text, settings)
    except Exception:
        response_payload = {}

    products_payload = response_payload.get("products") if isinstance(response_payload, dict) else None
    products: list[ProductCandidate] = []
    if isinstance(products_payload, list) and products_payload:
        try:
            products = [ProductCandidate.model_validate(item) for item in products_payload[:5]]
        except ValidationError:
            products = []

    if not products:
        products = fallback_candidates

    repaired_products = repair_candidate_urls(products, search_hits)
    filtered = filter_candidates_against_search_hits(repaired_products, allowed_urls)

    merged_products: list[ProductCandidate] = []
    seen_pairs: set[tuple[str, str]] = set()
    for candidate in [*filtered, *repaired_products, *fallback_candidates]:
        pair = (candidate.name.strip().lower(), candidate.source.strip().lower())
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        merged_products.append(candidate)

    ranked_products = rank_candidates_for_profile(merged_products, payload, profile)
    if len(ranked_products) >= 3:
        return ranked_products[:5]

    if fallback_candidates:
        fallback_ranked = rank_candidates_for_profile(fallback_candidates, payload, profile)
        if fallback_ranked:
            return fallback_ranked[:5]

    raise InvestigationError("Arama sonuçları yeterli sayıda anlamlı ürün üretmedi.")


async def curate_final(
    payload: InvestigateRequest,
    profile: PsychologicalProfile,
    candidates: list[ProductCandidate],
    settings: Settings,
    agents: list[AgentDescriptor],
    workflow: list[WorkflowStep],
) -> InvestigationResult:
    llm = build_chat_llm(settings, temperature=0.7)
    filters = build_filter_summary(payload)
    prompt = f"""
Sen Hediye Seçicisisin.
Aşağıdaki profil ve ürün adaylarını kullanarak en iyi 3 ürünü seç.
Ton premium, editoryal ve hafif dedektifvari olsun.
Yalnızca geçerli JSON dön.

Kurallar:
- Çıktının tamamı Türkçe olsun.
- Metinler gerçek bir editörün kaleminden çıkmış gibi dursun; çevrilmiş, robotik ya da fazla süslü bir dil kullanma.
- products dizisi tam olarak 3 ürün içersin.
- Ürün açıklamaları kısa, sade ve gündelik Türkçeyle yazılsın.
- Prompttaki ana meslek ve ilgi alanlarıyla en doğrudan uyuşan ürünleri seç; uzak çağrışımlı ürünleri ele.
- `editorial_intro` en fazla 4 cümle olsun.
- Her ürünün `why_it_matches` açıklaması tek cümle olsun.
- `why_it_matches` ürün adındaki nesneye sadık kalsın.
- Mümkün olduğunda üç ürün üç farklı kaynaktan gelsin; aynı siteyi yalnızca gerçekten güçlü bir gerekçe varsa tekrar kullan.
- Alışveriş sitesi dışındaki hiçbir kaynağı kullanma.
- Doğrudan ürün linki yoksa yalnızca mevcut aday havuzundaki koleksiyon, butik mağaza veya editör seçkisi fallbacklerini kullan.
- Seçimlerinde kullanıcının bütçe ve bölge tercihini koru.
- Her ürün için `candidate_index` ver ve yalnızca mevcut adaylardan seçim yap.
- Yeni ürün uydurma, link değiştirme, kaynak değiştirme.
- Eğer aday bağlantısı tekil ürün değil de koleksiyon/liste sayfasıysa, bunu tek bir spesifik ürünmüş gibi anlatma.
- `comparison_note`, `matched_signals` ve `caveats` alanlarını koru.
- profile_summary en fazla 2 cümle, editorial_intro ise akıcı ama ölçülü bir paragraf olsun.

Kullanıcı girdisi:
{payload.brief}

Filtreler:
{json.dumps(filters, ensure_ascii=False, indent=2)}

Psikolojik profil:
{profile.model_dump_json(indent=2)}

Ürün adayları:
{json.dumps([item.model_dump(mode='json') for item in candidates], ensure_ascii=False, indent=2)}

JSON şeması:
{{
  "profile_summary": "string",
  "editorial_intro": "string",
  "markdown": "string",
  "products": [
    {{
      "name": "string",
      "candidate_index": 1,
      "why_it_matches": "string",
      "price_label": "string",
      "url": "https://example.com",
      "source": "string",
      "editorial_note": "string"
    }}
  ]
}}
"""
    fallback_payload = build_fallback_result_payload(payload, profile, candidates, filters, agents, workflow)

    response_payload: dict = {}
    try:
        response = await llm.ainvoke(prompt)
        raw_text = response.content if hasattr(response, "content") else str(response)
        response_payload = await extract_or_repair_json(raw_text, settings)
    except Exception:
        response_payload = {}

    if not isinstance(response_payload, dict):
        response_payload = {}

    curated_payload = response_payload.get("products")
    if not isinstance(curated_payload, list):
        curated_payload = []

    hydrated_products = hydrate_curated_products(curated_payload, candidates)
    diversified_products = diversify_curated_products(hydrated_products, candidates, 3)
    final_products = fill_missing_curated_products(diversified_products, candidates, 3)
    if len(final_products) < 3:
        final_products = fallback_payload["products"]

    rewritten_products = await rewrite_final_product_explanations(
        payload,
        profile,
        final_products[:3],
        settings,
    )

    result_payload = {
        **fallback_payload,
        **{k: v for k, v in response_payload.items() if k != "products"},
        "products": rewritten_products[:3],
        "tone_mode": response_payload.get("tone_mode") or fallback_payload["tone_mode"],
    }

    try:
        result = InvestigationResult.model_validate(result_payload)
    except ValidationError:
        result = InvestigationResult.model_validate(fallback_payload)

    result.products = result.products[:3]
    return result
