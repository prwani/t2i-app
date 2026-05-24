"""Helpers for JSON-producing Azure OpenAI evaluation calls."""

import json
from typing import Any

from openai import AsyncOpenAI


async def create_json_chat_completion(
    client: AsyncOpenAI,
    *,
    model: str,
    is_o_series: bool,
    instructions: str,
    user_content: str | list[dict[str, Any]],
    max_tokens: int = 2000,
) -> tuple[dict[str, Any], Any]:
    """Call chat completions and parse the first JSON object response."""

    role = "developer" if is_o_series else "system"
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": role, "content": instructions},
            {"role": "user", "content": user_content},
        ],
        "response_format": {"type": "json_object"},
    }
    if is_o_series:
        kwargs["max_completion_tokens"] = max_tokens
        kwargs["reasoning_effort"] = "low"
    elif model.startswith("gpt-5"):
        kwargs["max_completion_tokens"] = max_tokens
    else:
        kwargs["max_tokens"] = max_tokens
        kwargs["temperature"] = 0.1

    response = await client.chat.completions.create(**kwargs)
    content = response.choices[0].message.content
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Azure OpenAI response did not include JSON content")
    parsed = parse_json_object(content)
    if not isinstance(parsed, dict):
        raise ValueError("Azure OpenAI response JSON must be an object")
    return parsed, response


def parse_json_object(content: str) -> dict[str, Any]:
    """Parse a JSON object, tolerating code fences or short explanatory wrappers."""

    stripped = content.strip()
    candidates = [stripped]
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        candidates.append("\n".join(lines).strip())

    object_text = _extract_first_json_object(stripped)
    if object_text is not None:
        candidates.append(object_text)

    for candidate in candidates:
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
        raise ValueError("Azure OpenAI response JSON must be an object")
    raise ValueError("Azure OpenAI response was not valid JSON")


def _extract_first_json_object(content: str) -> str | None:
    start = content.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escaped = False
    for index, character in enumerate(content[start:], start=start):
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return content[start : index + 1]
    return None
