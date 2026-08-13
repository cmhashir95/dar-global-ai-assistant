from __future__ import annotations

import json
from typing import Any

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

_client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def chat_completion(
    messages: list[dict],
    temperature: float = 0.2,
    max_tokens: int = 700,
    response_format: dict | None = None,
) -> str:
    """
    Single choke point for every LLM call in the app. Low default temperature
    on purpose: this is a grounded, task-oriented assistant, not a creative
    one, and lower temperature measurably reduces hallucinated specifics
    (prices, dates, amenities) in the generation step.
    """
    kwargs: dict[str, Any] = dict(
        model=settings.chat_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if response_format:
        kwargs["response_format"] = response_format

    completion = _client.chat.completions.create(**kwargs)
    return completion.choices[0].message.content or ""


def chat_completion_json(messages: list[dict], schema_name: str, json_schema: dict, **kwargs) -> dict:
    """
    Structured-output helper. Forces the model to return JSON that matches
    `json_schema`, which is how intent classification and slot-extraction
    avoid free-text parsing errors and reduce the chance of the model
    wandering off-format.
    """
    raw = chat_completion(
        messages=messages,
        response_format={
            "type": "json_schema",
            "json_schema": {"name": schema_name, "schema": json_schema, "strict": True},
        },
        **kwargs,
    )
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Extremely defensive fallback in case a non-strict-compatible model
        # wraps the JSON in prose or code fences.
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end != -1:
            return json.loads(raw[start : end + 1])
        raise
