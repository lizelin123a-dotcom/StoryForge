from typing import Callable, Any

from storyforge.domain.dissect.dissected_chapter import DissectedChapter
from storyforge.infrastructure.ai.openai_adapter import call_llm
from storyforge.application.dissect.services.common import extract_json_object

LLMCaller = Callable[[str, str, bool], str]

SYSTEM_PROMPT = """你是长篇网文宏观规划专家。
生成整本书宏观大纲：标题、总字数、分幕结构、每幕章节数。
如提供对标拆解结果，参考爽点频率、压爆节奏、核心矛盾推进。
必须只输出 JSON object。
"""


def generate_macro_outline(
    title: str,
    world_setting: str,
    characters: str,
    target_word_count: int,
    genre: str,
    dissected_chapters: list[DissectedChapter] | None = None,
    llm: LLMCaller = call_llm,
) -> dict[str, Any]:
    benchmark = [chapter.model_dump() for chapter in (dissected_chapters or [])]
    prompt = f"""请生成小说宏观大纲。
输出 JSON：
{{
  "title": "小说标题",
  "genre": "类型",
  "target_word_count": 1000000,
  "acts": [
    {{
      "index": 1,
      "name": "第一幕：立钩与入局",
      "function": "功能",
      "target_word_count": 300000,
      "core_conflict": "核心矛盾",
      "key_events": ["关键事件"],
      "chapter_count": 60
    }}
  ]
}}
标题：{title}
类型：{genre}
目标字数：{target_word_count}
世界观：{world_setting}
人物：{characters}
对标拆解：{benchmark}
"""
    try:
        return extract_json_object(llm(prompt, SYSTEM_PROMPT, True))
    except Exception:
        per_act = max(target_word_count // 3, 1)
        return {
            "title": title,
            "genre": genre,
            "target_word_count": target_word_count,
            "acts": [
                {"index": 1, "name": "第一幕：立钩与入局", "function": "建立世界观、主角目标与初始爽点", "target_word_count": per_act, "core_conflict": "主角目标与外部压迫首次碰撞", "key_events": ["开篇钩子", "金手指显露", "第一次打脸"], "chapter_count": max(per_act // 3000, 1)},
                {"index": 2, "name": "第二幕：升级与对抗", "function": "持续加压、扩大信息差、积累复利爽感", "target_word_count": per_act, "core_conflict": "主角成长速度与敌对势力围剿", "key_events": ["资源争夺", "身份反转", "阶段性碾压"], "chapter_count": max(per_act // 3000, 1)},
                {"index": 3, "name": "第三幕：爆发与收束", "function": "集中兑现伏笔并完成终局爽点", "target_word_count": target_word_count - per_act * 2, "core_conflict": "终极敌人与主角底层目标决战", "key_events": ["终局压迫", "底牌揭露", "最终爆发"], "chapter_count": max((target_word_count - per_act * 2) // 3000, 1)},
            ],
        }
