from langchain_tavily import TavilySearch
from langchain_openai import ChatOpenAI

from .config import Settings


def build_chat_llm(settings: Settings, temperature: float = 0.7) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.model_name,
        api_key="not-needed",
        base_url=settings.openrouter_base_url,
        temperature=temperature,
        default_headers={"Authorization": f"Key {settings.fal_key or ''}"},
    )


def build_search_tool(settings: Settings) -> TavilySearch:
    return TavilySearch(
        tavily_api_key=settings.tavily_api_key or "",
        max_results=settings.tavily_max_results,
        search_depth=settings.tavily_search_depth,
        include_answer=True,
        include_raw_content=False,
    )
