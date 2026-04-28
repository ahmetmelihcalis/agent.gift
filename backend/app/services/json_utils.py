import json

from ..agents import build_chat_llm
from ..config import Settings


class InvestigationError(Exception):
    """Known investigation failure."""


def extract_balanced_json_block(text: str) -> str:
    start = text.find("{")
    if start == -1:
        raise InvestigationError("Ajanlar geçerli bir JSON çıktısı üretemedi.")

    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        char = text[index]

        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]

    raise InvestigationError("Ajanlar geçerli bir JSON çıktısı üretemedi.")


def extract_json_payload(text: str) -> dict:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[1]
        stripped = stripped.rsplit("```", 1)[0].strip()

    json_block = extract_balanced_json_block(stripped)

    try:
        return json.loads(json_block)
    except json.JSONDecodeError:
        repaired = (
            json_block.replace(",}", "}")
            .replace(",]", "]")
            .replace("\t", " ")
            .strip()
        )
        try:
            return json.loads(repaired)
        except json.JSONDecodeError as exc:
            raise InvestigationError("JSON Parse error: Unable to parse JSON string") from exc


async def extract_or_repair_json(text: str, settings: Settings) -> dict:
    try:
        return extract_json_payload(text)
    except InvestigationError:
        repair_llm = build_chat_llm(settings, temperature=0)
        repair_prompt = f"""
Asagidaki metni gecerli JSON olarak onar.
Kurallar:
- Yalnizca gecerli JSON don
- Aciklama, markdown, kod blogu ekleme
- Veri alanlarini koru, sadece parse edilebilir hale getir

Metin:
{text}
"""
        repaired_response = await repair_llm.ainvoke(repair_prompt)
        repaired_text = (
            repaired_response.content
            if hasattr(repaired_response, "content")
            else str(repaired_response)
        )
        return extract_json_payload(repaired_text)
