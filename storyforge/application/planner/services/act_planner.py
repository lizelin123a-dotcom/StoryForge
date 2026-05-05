from typing import Callable, Any

from storyforge.infrastructure.ai.openai_adapter import call_llm
from storyforge.application.dissect.services.common import extract_json_array

LLMCaller = Callable[[str, str, bool], str]

SYSTEM_PROMPT = """你是网文章节节拍规划专家。根据宏观大纲为每一幕规划章节节拍。
每章要标注序号、核心事件、字数目标、情绪基调。只输出 JSON。
"""


def generate_act_plans(macro_outline: dict[str, Any], llm: LLMCaller = call_llm) -> list[dict[str, Any]]:
    prompt = f"""请为宏观大纲生成幕级节拍。
输出 JSON：{{"acts": [{{"index": 1, "name": "幕名", "function": "功能", "core_conflict": "核心矛盾", "conflict_evolution": ["演进"], "chapters": [{{"chapter_index": 1, "core_event": "核心事件", "target_word_count": 3000, "emotion_tone": "憋屈到爽"}}]}}]}}
宏观大纲：{macro_outline}
"""
    try:
        return extract_json_array(llm(prompt, SYSTEM_PROMPT, True))
    except Exception:
        acts: list[dict[str, Any]] = []
        global_chapter = 1
        for act in macro_outline.get("acts", []):
            chapter_count = min(int(act.get("chapter_count", 6)), 9)
            chapters = []
            for local_index in range(chapter_count):
                chapters.append({
                    "chapter_index": global_chapter,
                    "core_event": f"{act.get('name', '幕')}关键事件推进{local_index + 1}",
                    "target_word_count": 3000,
                    "emotion_tone": "压抑铺垫→期待→爽点兑现",
                })
                global_chapter += 1
            acts.append({
                "index": act.get("index", len(acts) + 1),
                "name": act.get("name", "未命名幕"),
                "function": act.get("function", "推进主线"),
                "core_conflict": act.get("core_conflict", "主角目标与阻碍冲突"),
                "conflict_evolution": ["引出矛盾", "连续加压", "阶段爆发"],
                "chapters": chapters,
            })
        return acts
