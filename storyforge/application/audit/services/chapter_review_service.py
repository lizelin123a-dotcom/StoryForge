from typing import Any, Callable

from storyforge.application.analyst.services.information_gap_service import analyze_information_gap
from storyforge.application.analyst.services.rhythm_detector import detect_rhythm
from storyforge.application.analyst.services.shuang_point_analyzer import analyze_shuang_points
from storyforge.application.dissect.services.common import extract_json_object
from storyforge.infrastructure.ai.openai_adapter import call_llm

LLMCaller = Callable[[str, str, bool], str]
SYSTEM_PROMPT = """你是长篇网文章末综合审阅专家。
一次性完成摘要、关键事件、人物三元组、伏笔台账、故事线、爽点、节奏、信息差分析。
必须只输出 JSON object，字段完整。
"""


def review_chapter(
    novel_id: str,
    chapter_index: int,
    chapter_text: str,
    previous_summaries: list[str] | None = None,
    foreshadowing_ledger: dict[str, Any] | None = None,
    llm: LLMCaller = call_llm,
) -> dict[str, Any]:
    prompt = f"""请对本章做章末综合审阅。一次 LLM 调用完成所有分析。
输出 JSON：
{{
  "chapter_summary": "本章摘要",
  "key_events": ["关键事件"],
  "triples": [{{"subject": "谁", "action": "做了什么", "object": "对谁/什么"}}],
  "foreshadowing": {{
    "new_hooks": [{{"description": "新伏笔", "expected_closure_chapter": 10}}],
    "closed_hooks": [{{"description": "消费伏笔", "opened_in_chapter": 1}}],
    "still_open": [{{"description": "仍未回收伏笔", "age_chapters": 2}}]
  }},
  "storyline_progress": "故事线进展",
  "shuang_analysis": {{"types_used": ["规则内打脸"], "main_type": "规则内打脸", "frequency": {{"规则内打脸": 1}}}},
  "rhythm": {{"pattern": "匹配/部分匹配/不匹配", "stage_word_counts": {{"压": 1000, "安全期": 300, "爆发": 500}}, "warnings": []}},
  "information_gap": {{"gaps": [{{"type": "reader_knows", "description": "信息差", "quality": "高"}}], "no_gap_warning": false, "suggestions": []}}
}}
小说ID：{novel_id}
章节序号：{chapter_index}
前文摘要：{previous_summaries or []}
伏笔台账：{foreshadowing_ledger or {}}
本章正文：
{chapter_text}
"""
    try:
        data = extract_json_object(llm(prompt, SYSTEM_PROMPT, True))
        return _normalize_review(data)
    except Exception:
        shuang = analyze_shuang_points(chapter_text, llm)
        rhythm = detect_rhythm(chapter_text, llm)
        gap = analyze_information_gap(chapter_text, llm)
        return _normalize_review({
            "chapter_summary": chapter_text[:120],
            "key_events": [line.strip() for line in chapter_text.splitlines() if line.strip()][:5],
            "triples": [],
            "foreshadowing": {"new_hooks": [], "closed_hooks": [], "still_open": list((foreshadowing_ledger or {}).get("still_open", []))},
            "storyline_progress": "本章推进了当前冲突与角色行动",
            "shuang_analysis": {"types_used": list(shuang.get("frequency", {}).keys()), "main_type": shuang.get("main_shuang", ""), "frequency": shuang.get("frequency", {})},
            "rhythm": {"pattern": rhythm.get("overall", "不匹配"), "stage_word_counts": {item.get("stage", "未知"): item.get("word_count", 0) for item in rhythm.get("stages", [])}, "warnings": rhythm.get("warnings", [])},
            "information_gap": gap,
        })


def _normalize_review(data: dict[str, Any]) -> dict[str, Any]:
    data.setdefault("chapter_summary", "")
    data.setdefault("key_events", [])
    data.setdefault("triples", [])
    data.setdefault("foreshadowing", {"new_hooks": [], "closed_hooks": [], "still_open": []})
    data.setdefault("storyline_progress", "")
    data.setdefault("shuang_analysis", {"types_used": [], "main_type": "", "frequency": {}})
    data.setdefault("rhythm", {"pattern": "不匹配", "stage_word_counts": {}, "warnings": []})
    data.setdefault("information_gap", {"gaps": [], "no_gap_warning": True, "suggestions": []})
    return data
