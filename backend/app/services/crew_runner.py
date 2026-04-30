import json
from collections.abc import AsyncIterator

from ..config import Settings
from ..schemas import AgentDescriptor, InvestigateRequest, WorkflowStep
from .agent_state import (
    build_agent_roster,
    build_workflow,
    mark_agent_state,
    prepare_crewai_runtime,
)
from .investigation_steps import curate_final, generate_profile, search_candidates


def format_sse(event: str, data: dict) -> dict[str, str]:
    return {"event": event, "data": json.dumps(data, ensure_ascii=False)}


async def run_investigation(
    payload: InvestigateRequest, settings: Settings
) -> AsyncIterator[dict[str, str]]:
    async for event in stream_investigation(payload, settings):
        yield event


def _agents_payload(agents: list[AgentDescriptor], workflow: list[WorkflowStep]) -> dict:
    return {
        "agents": [agent.model_dump(mode="json") for agent in agents],
        "workflow": [step.model_dump(mode="json") for step in workflow],
    }


def _log_payload(agent: str, role: str, agent_id: str, message: str) -> dict:
    return {
        "agent": agent,
        "role": role,
        "agent_id": agent_id,
        "message": message,
    }


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
    yield format_sse("agents", _agents_payload(agents, workflow))

    agents, workflow = mark_agent_state(
        agents,
        workflow,
        "profile_analyst",
        "working",
        "Kişiye dair ana ipuçları bir araya getiriliyor.",
    )
    yield format_sse("agents", _agents_payload(agents, workflow))
    yield format_sse(
        "log",
        _log_payload(
            "The Analyst",
            "Profil Analisti Ajan",
            "profile_analyst",
            "Anlatılanların arasından kişinin asıl eğilimlerini ayıklıyorum.",
        ),
    )

    agents, workflow = mark_agent_state(
        agents,
        workflow,
        "product_hunter",
        "working",
        "Sıradan seçenekleri eleyip daha güçlü ürünler aranıyor.",
    )
    yield format_sse("agents", _agents_payload(agents, workflow))
    yield format_sse(
        "log",
        _log_payload(
            "Finder Fox",
            "Ürün Tarama Ajanı",
            "product_hunter",
            "Herkesin gördüğü ürünlere değil, daha ilginç ürünlere bakıyorum.",
        ),
    )

    agents, workflow = mark_agent_state(
        agents,
        workflow,
        "gift_selector",
        "working",
        "En güçlü seçenekler seçilip son anlatı kuruluyor.",
    )
    yield format_sse("agents", _agents_payload(agents, workflow))
    yield format_sse(
        "log",
        _log_payload(
            "Mr. Decision",
            "Değerlendirme ve Raporlama Ajanı",
            "gift_selector",
            "Bulduğumuz ürünleri tartıp en yerinde üçlüyü seçiyorum.",
        ),
    )

    try:
        prepare_crewai_runtime()
        profile = await generate_profile(payload, settings)
        agents, workflow = mark_agent_state(
            agents,
            workflow,
            "profile_analyst",
            "done",
            "Kişinin temel eğilimleri ve hassas noktaları netleşti.",
        )
        yield format_sse("agents", _agents_payload(agents, workflow))

        candidates = await search_candidates(payload, profile, settings)
        agents, workflow = mark_agent_state(
            agents,
            workflow,
            "product_hunter",
            "done",
            "Güçlü ürünler toplandı, zayıf kalan seçenekler elendi.",
        )
        yield format_sse("agents", _agents_payload(agents, workflow))

        result = await curate_final(payload, profile, candidates, settings, agents, workflow)
        agents, workflow = mark_agent_state(
            agents,
            workflow,
            "gift_selector",
            "done",
            "Son öneriler hazır; paylaşılabilecek duruma geldi.",
        )
        result.agents = agents
        result.workflow = workflow
    except Exception as exc:
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
