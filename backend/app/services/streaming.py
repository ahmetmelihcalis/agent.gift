import json
from collections.abc import AsyncIterator


def format_sse(event: str, data: dict) -> dict[str, str]:
    return {"event": event, "data": json.dumps(data, ensure_ascii=False)}


async def emit_status(status: str, message: str) -> AsyncIterator[dict[str, str]]:
    yield format_sse("status", {"status": status, "message": message})


async def emit_log(agent: str, message: str) -> AsyncIterator[dict[str, str]]:
    yield format_sse("log", {"agent": agent, "message": message})
