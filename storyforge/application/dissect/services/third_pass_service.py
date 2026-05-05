from typing import Callable

from storyforge.domain.dissect.dissected_chapter import DissectedChapter, UnitStructure
from storyforge.infrastructure.ai.openai_adapter import call_llm

from .common import clamp_window, extract_json_array, split_chapters

LLMCaller = Callable[[str, str, bool], str]

SYSTEM_PROMPT = """你是网文标书拆解专家，执行三遍拆书法的第三遍单元结构模式。
以每个爽点为节点，拆出阻碍/支线支持/收获/突破/单元字数。
必须只输出 JSON object 或 JSON array，不要解释。
"""


def run_third_pass(raw_text: str, chapters: list[DissectedChapter], llm: LLMCaller = call_llm) -> list[UnitStructure]:
    chapter_texts = {index: content for index, _title, content, _offset in split_chapters(raw_text)}
    units: list[UnitStructure] = []
    for chapter in chapters:
        content = chapter_texts.get(chapter.chapter_index, raw_text)
        for point in chapter.shuang_points:
            window = clamp_window(content, point.position_start, point.position_end, 2500, 1500)
            prompt = f"""请围绕该爽点拆一个独立剧情单元。
输出 JSON：{{"unit_structures": [{{"obstacle": "阻碍", "side_support": "支线支持", "harvest": "收获", "breakthrough": "突破方式", "word_count": 1200}}]}}
爽点：{point.model_dump_json(ensure_ascii=False)}
上下文：
{window}
"""
            for item in extract_json_array(llm(prompt, SYSTEM_PROMPT, True)):
                units.append(UnitStructure(**item))
    return units
