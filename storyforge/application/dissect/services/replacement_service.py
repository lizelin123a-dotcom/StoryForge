from typing import Callable

from storyforge.domain.dissect.replacement_table import ReplacementTable
from storyforge.infrastructure.ai.openai_adapter import call_llm

from .common import extract_json_object

LLMCaller = Callable[[str, str, bool], str]

SYSTEM_PROMPT = """你是网文对标置换专家。
原则：世界观只改不变，保留底层爽感逻辑只换表层表达；金手指拆融改：拆解机制→融合创新→改造适配。
输出 ReplacementTable 对应 JSON，不要解释。
"""


def generate_replacement_table(
    benchmark_summary: str,
    world_setting: str,
    golden_finger: str,
    power_system: str,
    conflict_system: str,
    character_settings: str,
    llm: LLMCaller = call_llm,
) -> ReplacementTable:
    prompt = f"""请基于对标书拆解摘要和用户新设定，生成“对标→置换”映射表。
输出 JSON：
{{
  "world_setting_replace": {{"原设定/底层逻辑": "新表层设定"}},
  "golden_finger_replace": {{"原机制": "拆融改后的新机制"}},
  "power_system_replace": {{"原升级逻辑": "新升级表达"}},
  "conflict_system_replace": {{"原矛盾": "新矛盾"}},
  "character_replace": {{"原角色功能": "新角色设定"}}
}}

对标书拆解摘要：
{benchmark_summary}

用户新世界观：{world_setting}
用户新金手指：{golden_finger}
用户新力量体系：{power_system}
用户新矛盾体系：{conflict_system}
用户新人物设定：{character_settings}
"""
    return ReplacementTable(**extract_json_object(llm(prompt, SYSTEM_PROMPT, True)))
