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
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError("Azure OpenAI response was not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError("Azure OpenAI response JSON must be an object")
    return parsed, response
