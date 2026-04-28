import os
from copy import deepcopy
from pathlib import Path
from typing import Literal

from ..schemas import AgentDescriptor, InvestigateRequest, WorkflowStep


AGENT_BLUEPRINTS = [
    {
        "id": "profile_analyst",
        "name": "The Analyst",
        "role": "Profil Analisti Ajan",
        "specialty": "Satır aralarında kalan ipuçlarını toplayıp kişinin eğilimlerini çözüyor.",
        "headline": "Kişinin nasıl biri olduğunu anlamaya çalışıyor.",
    },
    {
        "id": "product_hunter",
        "name": "Finder Fox",
        "role": "Ürün Tarama Ajanı",
        "specialty": "Sıradan seçenekleri eliyor, daha özgün ve alınabilir ürünler buluyor.",
        "headline": "Herkesin önüne çıkanları değil, asıl ilginç adayları topluyor.",
    },
    {
        "id": "gift_selector",
        "name": "Mr. Decision",
        "role": "Değerlendirme ve Raporlama Ajanı",
        "specialty": "En güçlü üç öneriyi ayıklayıp son dokunuşu yapıyor.",
        "headline": "Bulunan adayları tartıp en doğru önerileri hazırlıyor.",
    },
]

WORKFLOW_BLUEPRINTS = [
    {"id": "profile", "label": "Profil çıkarılıyor", "agent_id": "profile_analyst"},
    {"id": "hunt", "label": "Adaylar aranıyor", "agent_id": "product_hunter"},
    {"id": "select", "label": "Öneriler netleştiriliyor", "agent_id": "gift_selector"},
]


def prepare_crewai_runtime() -> None:
    crewai_home = Path("/tmp/agentic-gift-crewai-home")
    crewai_home.mkdir(parents=True, exist_ok=True)
    os.environ["HOME"] = str(crewai_home)
    os.environ["XDG_DATA_HOME"] = str(crewai_home)
    os.environ["CREWAI_STORAGE_DIR"] = "agentic-gift"
    os.environ["CREWAI_TRACING_ENABLED"] = "false"


def build_agent_roster() -> list[AgentDescriptor]:
    return [
        AgentDescriptor(
            id=item["id"],
            name=item["name"],
            role=item["role"],
            specialty=item["specialty"],
            status="idle",
            headline=item["headline"],
        )
        for item in AGENT_BLUEPRINTS
    ]


def build_workflow() -> list[WorkflowStep]:
    return [
        WorkflowStep(
            id=item["id"],
            label=item["label"],
            status="idle",
            agent_id=item["agent_id"],
        )
        for item in WORKFLOW_BLUEPRINTS
    ]


def mark_agent_state(
    agents: list[AgentDescriptor],
    workflow: list[WorkflowStep],
    agent_id: str,
    status: Literal["idle", "working", "done"],
    note: str,
) -> tuple[list[AgentDescriptor], list[WorkflowStep]]:
    next_agents = deepcopy(agents)
    next_workflow = deepcopy(workflow)

    for agent in next_agents:
        if agent.id == agent_id:
            agent.status = status
            agent.latest_note = note

    for step in next_workflow:
        if step.agent_id == agent_id:
            step.status = status

    return next_agents, next_workflow


def build_filter_summary(payload: InvestigateRequest) -> dict[str, str | list[str]]:
    return {
        "budget": payload.budget or "Belirtilmedi",
        "region": payload.region or "Global",
        "delivery_speed": payload.delivery_speed or "Esnek",
        "tone_mode": payload.tone_mode or "Editoryal",
        "avoid_categories": payload.avoid_categories or [],
        "refine_instruction": payload.refine_instruction or "Yok",
    }
