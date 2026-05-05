from typing import Callable

from storyforge.domain.dissect.dissected_chapter import DissectedChapter
from storyforge.infrastructure.ai.openai_adapter import call_llm

from .common import clamp_window, extract_json_object, split_chapters

LLMCaller = Callable[[str, str, bool], str]

SYSTEM_PROMPT = """你是网文标书拆解专家，执行三遍拆书法的第二遍拆解模式。
对每个爽点前后精细分析，标记压/抬段落，分析信息差：读者知道什么 vs 角色知道什么。
必须只输出 JSON object，不要解释。
"""


def run_second_pass(raw_text: str, chapters: list[DissectedChapter], llm: LLMCaller = call_llm) -> list[DissectedChapter]:
    chapter_texts = {index: content for index, _title, content, _offset in split_chapters(raw_text)}
    enhanced: list[DissectedChapter] = []
    for chapter in chapters:
        content = chapter_texts.get(chapter.chapter_index, raw_text)
        enhanced_points = []
        for point in chapter.shuang_points:
            window = clamp_window(content, point.position_start, point.position_end, 2000, 1000)
            prompt = f"""请对爽点做第二遍精细拆解。
输出 JSON：
{{
  "pressure_ranges": [{{"start": 0, "end": 100, "summary": "压的内容"}}],
  "lift_ranges": [{{"start": 100, "end": 200, "summary": "抬的内容"}}],
  "emotion_curve_detail": [{{"range": "0-100", "emotion": "憋屈", "reason": "原因"}}],
  "information_gap": {{"reader_knows": ["读者知道"], "character_knows": ["角色知道"], "usage": "信息差用法"}},
  "rhythm_pattern": "压→压→安全期→压→压→爆发 的匹配情况"
}}
爽点：{point.model_dump_json(ensure_ascii=False)}
上下文：
{window}
"""
            data = extract_json_object(llm(prompt, SYSTEM_PROMPT, True))
            point_data = point.model_dump()
            point_data["second_pass"] = data
            enhanced_points.append(point_data)
        curve = dict(chapter.emotional_curve)
        curve["second_pass"] = {"shuang_points_detail": enhanced_points}
        enhanced.append(chapter.model_copy(update={"emotional_curve": curve}))
    return enhanced
