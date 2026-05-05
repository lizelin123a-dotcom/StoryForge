from typing import Callable

from storyforge.domain.dissect.dissected_chapter import DissectedChapter, UnitStructure
from storyforge.domain.material.character_card import CharacterCard
from storyforge.domain.material.material_bank import MaterialBank
from storyforge.infrastructure.ai.openai_adapter import call_llm

from .common import extract_json_object

LLMCaller = Callable[[str, str, bool], str]

SYSTEM_PROMPT = """你是网文素材库整理专家。
从拆解章节中提取人物、场景、矛盾、爽点分类、单元剧情。输出结构化 JSON，不要解释。
"""


def integrate_material_bank(
    source_novel_id: str,
    chapters: list[DissectedChapter],
    unit_structures: list[UnitStructure] | None = None,
    llm: LLMCaller = call_llm,
) -> MaterialBank:
    chapter_payload = [chapter.model_dump() for chapter in chapters]
    unit_payload = [unit.model_dump() for unit in (unit_structures or [])]
    prompt = f"""请遍历拆解结果，生成素材库。
输出 JSON：
{{
  "characters": [{{
    "name": "姓名", "identity": "身份", "appearance": "外貌", "personality_tags": ["标签"],
    "ability": "能力", "background": "背景", "current_goal": "当前目标",
    "relationships": ["关系"], "conflict_points": ["矛盾点"], "growth_arc": "成长弧"
  }}],
  "scene_settings": [{{"name": "场景", "function": "剧情功能", "atmosphere": "氛围", "conflicts": ["矛盾"]}}],
  "shuang_categories": {{"爽点类型": 3}},
  "conflict_relations": [{{"conflict": "矛盾", "parties": ["相关方"], "status": "状态"}}],
  "unit_plots": [{{"obstacle": "阻碍", "side_support": "支线支持", "harvest": "收获", "breakthrough": "突破"}}]
}}

章节拆解：{chapter_payload}
单元结构：{unit_payload}
"""
    data = extract_json_object(llm(prompt, SYSTEM_PROMPT, True))
    characters = [CharacterCard(**item).model_dump() for item in data.get("characters", [])]
    items = {
        "characters": characters,
        "scene_settings": data.get("scene_settings", []),
        "shuang_categories": data.get("shuang_categories", {}),
        "conflict_relations": data.get("conflict_relations", []),
        "unit_plots": data.get("unit_plots", []),
        "raw": data,
    }
    return MaterialBank(id=f"material-{source_novel_id}", name="标书拆解素材库", items=items)
