from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    app_name: str = "agent.gift API"
    frontend_origin: str = Field(default="http://localhost:3000", alias="FRONTEND_ORIGIN")
    fal_key: str | None = Field(default=None, alias="FAL_KEY")
    tavily_api_key: str | None = Field(default=None, alias="TAVILY_API_KEY")
    model_name: str = Field(default="openai/gpt-4.1-mini", alias="MODEL_NAME")
    tavily_search_depth: str = Field(default="basic", alias="TAVILY_SEARCH_DEPTH")
    tavily_max_results: int = Field(default=8, alias="TAVILY_MAX_RESULTS")
    openrouter_base_url: str = Field(
        default="https://fal.run/openrouter/router/openai/v1",
        alias="OPENROUTER_BASE_URL",
    )

    model_config = SettingsConfigDict(
        env_file=str(ROOT_ENV_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
