import json
import os
import time
from typing import Any

import httpx


class LLMError(RuntimeError):
    pass


def call_llm(
    prompt: str,
    system_prompt: str = "",
    json_mode: bool = False,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> str:
    key = api_key or os.getenv("OPENAI_API_KEY", "")
    if not key:
        raise LLMError("OPENAI_API_KEY is not configured")

    url_base = (base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
    model_name = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    url = f"{url_base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload: dict[str, Any] = {
        "model": model_name,
        "messages": messages,
        "temperature": 0.2,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return str(data["choices"][0]["message"]["content"])
        except (httpx.TimeoutException, httpx.HTTPError, KeyError, IndexError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2**attempt)
                continue
            break

    raise LLMError(f"LLM call failed after 3 attempts: {last_error}")
