import re
from typing import Any, Callable

from storyforge.application.dissect.services.common import extract_json_object
from storyforge.infrastructure.ai.openai_adapter import call_llm

LLMCaller = Callable[[str, str, bool], str]
SYSTEM_PROMPT = """你是网文章节节奏检测专家。检测是否符合 压→压→安全期→压→压→爆发。只输出 JSON object。
"""


def detect_rhythm(text: str, llm: LLMCaller = call_llm) -> dict[str, Any]:
    prompt = f"""请检测章节节奏。
输出 JSON：{{"overall": "匹配/部分匹配/不匹配", "stages": [{{"stage": "压", "start": 0, "end": 100, "word_count": 100, "summary": "阶段摘要"}}], "setup_ratio": 2.0, "consecutive_flat_chapters": 0, "warnings": []}}
节奏公式：压 → 压 → 安全期 → 压 → 压 → 爆发。
正文：
{text}
"""
    try:
        data = extract_json_object(llm(prompt, SYSTEM_PROMPT, True))
        data.setdefault("warnings", [])
        return data
    except Exception:
        return _fallback_rhythm(text)


def detect_rhythm_for_texts(texts: list[str], llm: LLMCaller = call_llm) -> list[dict[str, Any]]:
    results = []
    flat_count = 0
    for text in texts:
        result = detect_rhythm(text, llm)
        has_burst = any(stage.get("stage") == "爆发" for stage in result.get("stages", [])) or any(word in text for word in ["反杀", "打脸", "爆发", "震惊"])
        flat_count = 0 if has_burst else flat_count + 1
        result["consecutive_flat_chapters"] = flat_count
        results.append(result)
    return results


def _fallback_rhythm(text: str) -> dict[str, Any]:
    parts = [part for part in re.split(r"\n+", text) if part.strip()] or [text]
    burst_keywords = ["反杀", "打脸", "爆发", "震惊", "揭露"]
    burst_index = next((i for i, part in enumerate(parts) if any(word in part for word in burst_keywords)), len(parts) - 1)
    stages = []
    cursor = 0
    for i, part in enumerate(parts):
        stage = "爆发" if i >= burst_index else ("安全期" if i == max(0, burst_index - 2) else "压")
        start = text.find(part, cursor)
        end = start + len(part)
        cursor = end
        stages.append({"stage": stage, "start": max(start, 0), "end": end, "word_count": len(part), "summary": part[:40]})
    setup = sum(item["word_count"] for item in stages if item["stage"] != "爆发")
    burst = max(sum(item["word_count"] for item in stages if item["stage"] == "爆发"), 1)
    warnings = [] if setup > burst else ["爽点前铺垫不足，爆发段字数超过铺垫段"]
    return {"overall": "部分匹配" if stages else "不匹配", "stages": stages, "setup_ratio": round(setup / burst, 2), "consecutive_flat_chapters": 0, "warnings": warnings}
