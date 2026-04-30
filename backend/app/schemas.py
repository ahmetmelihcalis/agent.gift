from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class InvestigateRequest(BaseModel):
    brief: str = Field(min_length=10, description="Gift investigation prompt from the user.")
    budget: str | None = None
    delivery_speed: str | None = None
    tone_mode: str | None = None
    avoid_categories: list[str] = Field(default_factory=list)
    refine_instruction: str | None = None


class PsychologicalProfile(BaseModel):
    inferred_persona: str
    obsessions: list[str]
    aversions: list[str]
    hidden_hooks: list[str]
    gifting_risks: list[str]
    tone_notes: str


class AgentDescriptor(BaseModel):
    id: str
    name: str
    role: str
    specialty: str
    status: Literal["idle", "working", "done"]
    headline: str
    latest_note: str | None = None


class WorkflowStep(BaseModel):
    id: str
    label: str
    status: Literal["idle", "working", "done"]
    agent_id: str


class ProductCandidate(BaseModel):
    name: str
    why_it_matches: str
    price_label: str = "Bulunamadi"
    url: HttpUrl | str
    source: str
    editorial_note: str
    matched_signals: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    comparison_note: str = ""


class InvestigationResult(BaseModel):
    session_id: str
    profile_summary: str
    editorial_intro: str
    markdown: str
    tone_mode: str
    applied_filters: dict[str, str | list[str]]
    profile_snapshot: PsychologicalProfile
    agents: list[AgentDescriptor]
    workflow: list[WorkflowStep]
    products: list[ProductCandidate]


class StreamEvent(BaseModel):
    event: Literal["status", "log", "result", "error", "agents"]
    data: dict
