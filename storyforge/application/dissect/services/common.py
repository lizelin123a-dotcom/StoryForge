import json
import re
from typing import Any


def extract_json_object(text: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("LLM response does not contain a JSON object")
    data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise ValueError("LLM response JSON is not an object")
    return data


def extract_json_array(text: str) -> list[Any]:
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("items", "chapters", "unit_structures", "characters", "scenes"):
                value = data.get(key)
                if isinstance(value, list):
                    return value
    except json.JSONDecodeError:
        pass

    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        raise ValueError("LLM response does not contain a JSON array")
    data = json.loads(match.group(0))
    if not isinstance(data, list):
        raise ValueError("LLM response JSON is not an array")
    return data


def split_chapters(raw_text: str) -> list[tuple[int, str, str, int]]:
    pattern = re.compile(r"(?m)^(第[一二三四五六七八九十百千万0-9]+章[^\n]*|Chapter\s+\d+[^\n]*)")
    matches = list(pattern.finditer(raw_text))
    if not matches:
        return [(0, "全文", raw_text.strip(), 0)] if raw_text.strip() else []

    chapters: list[tuple[int, str, str, int]] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(raw_text)
        title = match.group(1).strip()
        content = raw_text[start:end].strip()
        chapters.append((index, title, content, start))
    return chapters


def clamp_window(text: str, start: int, end: int, before: int = 2000, after: int = 1000) -> str:
    left = max(0, start - before)
    right = min(len(text), end + after)
    return text[left:right]
