from typing import Any, Callable

from storyforge.application.dissect.services.common import extract_json_object
from storyforge.infrastructure.ai.openai_adapter import call_llm

LLMCaller = Callable[[str, str, bool], str]
SYSTEM_PROMPT = """你是长篇网文矛盾演进追踪专家。追踪矛盾新建/激化/化解/升级，验证主矛盾解决后子矛盾是否升级。只输出 JSON object。
"""


def track_conflicts(
    chapter_text: str,
    chapter_index: int,
    previous_conflicts: list[dict[str, Any]] | None = None,
    llm: LLMCaller = call_llm,
) -> dict[str, Any]:
    prompt = f"""请追踪本章矛盾演进。
输出 JSON：{{"current_conflicts": [{{"conflict": "矛盾", "status": "新建/激化/化解/升级", "age_chapters": 1}}], "resolved": [{{"conflict": "已解决矛盾", "resolved_in_chapter": {chapter_index}, "evolved_to": "升级为哪个子矛盾"}}], "warnings": []}}
章节序号：{chapter_index}
历史矛盾：{previous_conflicts or []}
正文：
{chapter_text}
"""
    try:
        data = extract_json_object(llm(prompt, SYSTEM_PROMPT, True))
        data.setdefault("current_conflicts", [])
        data.setdefault("resolved", [])
        data.setdefault("warnings", [])
        return data
    except Exception:
        return _fallback_conflicts(chapter_text, chapter_index, previous_conflicts or [])


def _fallback_conflicts(text: str, chapter_index: int, previous: list[dict[str, Any]]) -> dict[str, Any]:
    current = []
    warnings = []
    if any(word in text for word in ["冲突", "敌", "威胁", "嘲笑", "争夺", "反派"]):
        current.append({"conflict": "主角目标与外部压迫冲突", "status": "激化" if previous else "新建", "age_chapters": 1})
    if not current:
        warnings.append("本章未检测到明显新矛盾或矛盾推进")
    if len(previous) >= 3 and not current:
        warnings.append("连续章节矛盾推进不足")
    return {"current_conflicts": current, "resolved": [], "warnings": warnings}
