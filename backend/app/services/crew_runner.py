import asyncio
import json
import uuid
from collections.abc import AsyncIterator

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
from .agent_state import (
    build_agent_roster,
    build_filter_summary,
    build_workflow,
    mark_agent_state,
    prepare_crewai_runtime,
)
from .curation import fill_missing_curated_products, hydrate_curated_products
from .json_utils import InvestigationError, extract_or_repair_json
from .search_helpers import (
    build_search_queries,
    filter_candidates_against_search_hits,
    flatten_search_hits,
)
from .streaming import format_sse
from .url_filters import repair_candidate_urls


async def _generate_profile(payload: InvestigateRequest, settings: Settings) -> PsychologicalProfile:
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
    payload = await extract_or_repair_json(raw_text, settings)
    try:
        return PsychologicalProfile.model_validate(payload)
    except ValidationError as exc:
        raise InvestigationError("Psikolojik profil beklenen formata uymuyor.") from exc


async def _search_candidates(
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

    direct_hits = flatten_search_hits(search_results)
    if len(direct_hits) < 2 and second_pass_queries:
        for query in second_pass_queries:
            result = await asyncio.to_thread(search_tool.invoke, query)
            search_results.append({"query": query, "results": result})
        direct_hits = flatten_search_hits(search_results)

    search_hits = direct_hits
    if len(search_hits) < 2:
        search_hits = flatten_search_hits(search_results, allow_fallback=True)
    if len(search_hits) < 2:
        search_hits = flatten_search_hits(
            search_results, allow_fallback=True, allow_browseable=True
        )

    if len(search_hits) < 1:
        raise InvestigationError("Arama sonuçları yeterince güçlü bağlantı üretmedi.")

    allowed_urls = {item["url"] for item in search_hits}

    prompt = f"""
Sen Ürün Avcısısın.
Kupa, tişört, jenerik mum, genel hediye kartı, Amazon arama sayfası, genel kategori sayfası ve tembel seçimleri reddet.
Aşağıdaki profil ve arama sonuçlarını kullanarak tam 5 adet niş, şaşırtıcı hediye adayı seç.
Yalnızca geçerli JSON dön.

Kurallar:
- Çıktı dili tamamen Türkçe olsun.
- Türkçesi çevrilmiş gibi duran kalıplardan kaçın; doğal ve yaşayan bir dil kullan.
- Ürünler gerçekten satın alınabilir ve karakterli olsun; mümkün olduğunda doğrudan ürün sayfasını tercih et.
- Amazon arama sonucu, Etsy market sayfası, kategori sayfası, koleksiyon sayfası veya arama filtresi içeren link verme.
- Doğrudan ürün sayfası yoksa, profile güçlü biçimde uyan ve ürünleri açıkça gösteren seçili koleksiyon ya da mağaza sayfasını kullanabilirsin.
- Eğer kullandığın bağlantı tek bir ürüne değil, koleksiyon ya da liste sayfasına açılıyorsa ürün adı uydurma.
- Böyle durumlarda `name` alanı sayfanın gerçekten sunduğu ürün grubunu ya da koleksiyon başlığını yansıtsın; görünmeyen bir ürün modeli, atkı, şarj cihazı ya da aksesuar icat etme.
- `url` alanı, aşağıdaki arama hitlerinden birinin URL'si ile birebir aynı olmak zorunda.
- Eğer yalnızca koleksiyon veya seçili liste sayfası varsa, bunu ancak gerçekten profile uygun ürünleri bir araya getiren güçlü bir kaynak olarak kullan.
- Aynı fikrin varyasyonlarını sıralama.
- Çok genel "ödül plaketi", "standart poster", "jenerik aksesuar" gibi zayıf seçimleri ele.
- Her adayda neden uygun olduğunu kısa ama sahici bir Türkçeyle açıkla.
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
    response = await llm.ainvoke(prompt)
    raw_text = response.content if hasattr(response, "content") else str(response)
    payload = await extract_or_repair_json(raw_text, settings)
    products_payload = payload.get("products")
    if not isinstance(products_payload, list) or not products_payload:
        raise InvestigationError("Urun avcisi gecerli bir aday listesi uretemedi.")

    try:
        products = [ProductCandidate.model_validate(item) for item in products_payload[:5]]
    except ValidationError as exc:
        raise InvestigationError("Urun adaylari beklenen formata uymuyor.") from exc

    repaired_products = repair_candidate_urls(products, search_hits)
    filtered = filter_candidates_against_search_hits(repaired_products, allowed_urls)
    if len(filtered) >= 3:
        return filtered[:5]

    unique_products: list[ProductCandidate] = []
    seen_pairs: set[tuple[str, str]] = set()
    for product in repaired_products:
        pair = (product.name.strip().lower(), product.source.strip().lower())
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        unique_products.append(product)

    if len(unique_products) < 3:
        raise InvestigationError("Urun avcisi yeterli sayida anlamli aday üretemedi.")

    return unique_products[:5]


async def _curate_final(
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
- Neden bu seçimlerin klişe olmadığını hissettir.
- Ürün açıklamaları kısa ama güçlü olsun.
- Genel mağaza araması, kategori, market, koleksiyon veya arama sonucu linki kullanma.
- Her ürün için `candidate_index` ver ve yalnızca mevcut adaylardan seçim yap.
- Yeni ürün uydurma, link değiştirme, kaynak değiştirme.
- Eğer aday bağlantısı tekil ürün değil de koleksiyon/liste sayfasıysa, bunu tek bir spesifik ürünmüş gibi anlatma.
- profile_summary, editorial_intro ve markdown alanları akıcı Türkçe karakterlerle yazılsın.
- `comparison_note`, `matched_signals` ve `caveats` alanlarını koru.
- "şu ürün harika bir seçimdir" gibi yapay pazarlama kalıplarından kaçın.
- profile_summary en fazla 2 cümle, editorial_intro ise akıcı ve doğal bir paragraf olsun.

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
    response = await llm.ainvoke(prompt)
    raw_text = response.content if hasattr(response, "content") else str(response)
    payload = await extract_or_repair_json(raw_text, settings)
    curated_payload = payload.get("products")
    if not isinstance(curated_payload, list) or not curated_payload:
        raise InvestigationError("Kurator gecerli bir secim listesi uretemedi.")

    hydrated_products = hydrate_curated_products(curated_payload, candidates)
    payload["products"] = fill_missing_curated_products(hydrated_products, candidates, 3)
    payload["session_id"] = str(uuid.uuid4())
    payload["tone_mode"] = payload.get("tone_mode") or (payload.get("applied_filters", {}) or {}).get("tone_mode") or (payload.get("tone_mode") or filters["tone_mode"])
    payload["applied_filters"] = filters
    payload["profile_snapshot"] = profile.model_dump(mode="json")
    payload["agents"] = [agent.model_dump(mode="json") for agent in agents]
    payload["workflow"] = [step.model_dump(mode="json") for step in workflow]
    try:
        result = InvestigationResult.model_validate(payload)
    except ValidationError as exc:
        raise InvestigationError("Final rapor beklenen formata uymuyor.") from exc

    if len(result.products) < 3:
        raise InvestigationError("Küratör yeterli sayıda seçim tamamlayamadı.")

    result.products = result.products[:3]
    return result


async def run_investigation(
    payload: InvestigateRequest, settings: Settings
) -> AsyncIterator[dict[str, str]]:
    async for event in stream_investigation(payload, settings):
        yield event


async def stream_investigation(payload: InvestigateRequest, settings: Settings) -> AsyncIterator[dict[str, str]]:
    if not settings.fal_key or not settings.tavily_api_key:
        yield format_sse(
            "error",
            {"message": "Sistem şu an sonuç üretemedi. Gerekli anahtarlar eksik görünüyor."},
        )
        return

    agents = build_agent_roster()
    workflow = build_workflow()
    yield format_sse("status", {"status": "queued", "message": "Dosya açılıyor."})
    yield format_sse(
        "agents",
        {
            "agents": [agent.model_dump(mode="json") for agent in agents],
            "workflow": [step.model_dump(mode="json") for step in workflow],
        },
    )

    agents, workflow = mark_agent_state(
        agents,
        workflow,
        "profile_analyst",
        "working",
        "Kişiye dair ana ipuçları bir araya getiriliyor.",
    )
    yield format_sse(
        "agents",
        {
            "agents": [agent.model_dump(mode="json") for agent in agents],
            "workflow": [step.model_dump(mode="json") for step in workflow],
        },
    )
    yield format_sse(
        "log",
        {
            "agent": "The Analyst",
            "role": "Profil Analisti Ajan",
            "agent_id": "profile_analyst",
            "message": "Anlatılanların arasından kişinin asıl eğilimlerini ayıklıyorum.",
        },
    )

    agents, workflow = mark_agent_state(
        agents,
        workflow,
        "product_hunter",
        "working",
        "Sıradan seçenekleri eleyip daha güçlü adaylar aranıyor.",
    )
    yield format_sse(
        "agents",
        {
            "agents": [agent.model_dump(mode="json") for agent in agents],
            "workflow": [step.model_dump(mode="json") for step in workflow],
        },
    )
    yield format_sse(
        "log",
        {
            "agent": "Finder Fox",
            "role": "Ürün Tarama Ajanı",
            "agent_id": "product_hunter",
            "message": "Herkesin gördüğü ürünlere değil, daha ilginç adaylara bakıyorum.",
        },
    )

    agents, workflow = mark_agent_state(
        agents,
        workflow,
        "gift_selector",
        "working",
        "En güçlü seçenekler seçilip son anlatı kuruluyor.",
    )
    yield format_sse(
        "agents",
        {
            "agents": [agent.model_dump(mode="json") for agent in agents],
            "workflow": [step.model_dump(mode="json") for step in workflow],
        },
    )
    yield format_sse(
        "log",
        {
            "agent": "Mr. Decision",
            "role": "Değerlendirme ve Raporlama Ajanı",
            "agent_id": "gift_selector",
            "message": "Bulduğumuz adayları tartıp en yerinde üçlüyü seçiyorum.",
        },
    )

    try:
        prepare_crewai_runtime()
        profile = await _generate_profile(payload, settings)
        agents, workflow = mark_agent_state(
            agents,
            workflow,
            "profile_analyst",
            "done",
            "Kişinin temel eğilimleri ve hassas noktaları netleşti.",
        )
        yield format_sse(
            "agents",
            {
                "agents": [agent.model_dump(mode="json") for agent in agents],
                "workflow": [step.model_dump(mode="json") for step in workflow],
            },
        )
        candidates = await _search_candidates(payload, profile, settings)
        agents, workflow = mark_agent_state(
            agents,
            workflow,
            "product_hunter",
            "done",
            "Güçlü adaylar toplandı, zayıf kalan seçenekler elendi.",
        )
        yield format_sse(
            "agents",
            {
                "agents": [agent.model_dump(mode="json") for agent in agents],
                "workflow": [step.model_dump(mode="json") for step in workflow],
            },
        )
        result = await _curate_final(payload, profile, candidates, settings, agents, workflow)
        agents, workflow = mark_agent_state(
            agents,
            workflow,
            "gift_selector",
            "done",
            "Son öneriler hazır; paylaşılabilecek duruma geldi.",
        )
        result.agents = agents
        result.workflow = workflow
    except InvestigationError as exc:
        yield format_sse("error", {"message": "Sistem şu an sonuç üretemedi.", "detail": str(exc)})
        return
    except Exception as exc:  # pragma: no cover - third-party runtime safety
        yield format_sse(
            "error",
            {"message": "Sistem şu an sonuç üretemedi.", "detail": str(exc)},
        )
        return

    if not result.products:
        yield format_sse(
            "error",
            {"message": "Sistem şu an sonuç üretemedi.", "detail": "Uygun ürün bulunamadı."},
        )
        return

    yield format_sse("status", {"status": "completed", "message": "Dosya kapatıldı."})
    yield format_sse("result", result.model_dump(mode="json"))
