import uuid
from typing import Any, Callable

from storyforge.application.dissect.services.common import extract_json_array, extract_json_object
from storyforge.domain.node.node import ChapterNode
from storyforge.infrastructure.ai.openai_adapter import call_llm

LLMCaller = Callable[[str, str, bool], str]

NODE_TYPES = {"hook", "setup", "conflict", "pressure", "burst", "aftermath", "harvest", "newsetup"}
SEGMENT_FUNCTIONS = {"atmosphere", "character_beat", "dialogue_push", "action_beat", "revelation", "emotional_landing", "transition"}
SYSTEM_PROMPT = """你是章节级网文章纲规划专家。
你必须同时完成章节总控和节点规划：memo、emotional_design、5-9 个节点。
第一个节点 hook，至少一个 burst，最后一个 newsetup。
节点类型只能是 hook/setup/conflict/pressure/burst/aftermath/harvest/newsetup。
segment_function 只能是 atmosphere/character_beat/dialogue_push/action_beat/revelation/emotional_landing/transition。
必须输出 JSON object。
"""


def generate_chapter_outline(
    act_plan: dict[str, Any],
    chapter_index: int,
    chapter_function: str,
    llm: LLMCaller = call_llm,
) -> dict[str, Any]:
    prompt = f"""请为指定章节生成增强章纲。

输出 JSON object，格式：
{{
  "chapter_function": "本章在整卷中的功能",
  "narrative_pov": "第三人称有限/第一人称/全知",
  "memo": {{
    "current_task": "本章角色必须完成的具体任务",
    "reader_expectation": "读者此刻具体在等什么",
    "payoff_plan": {{"must_resolve": [], "must_hold": [], "partial_advance": []}},
    "downtime_functions": [],
    "key_choices": [],
    "required_changes": [],
    "prohibitions": []
  }},
  "emotional_design": {{
    "primary_mood": "主情绪",
    "mood_progression": ["起点", "转折", "落点"],
    "intensity_peak": "情绪峰值场景",
    "emotional_hook": "章尾读者最想知道的问题",
    "intensity_level": 6,
    "micro_payoffs": []
  }},
  "nodes": [
    {{
      "index": 1,
      "node_type": "hook",
      "segment_function": "atmosphere",
      "trigger_point": "触发点，要能写成具体场景",
      "emotion_purpose": "情绪目的",
      "reader_expectation": "读者期待",
      "what_to_write": "本节点具体写什么，场景笔记式，不要分析腔",
      "ends_with": "本节点结束时的具体画面或状态",
      "characters": [],
      "micro_payoff": "",
      "expected_word_count": 300
    }}
  ]
}}

要求：
1. 每章 5-9 个节点，每节点 200-500 字。
2. 开篇第一节点必须 hook；整章至少一个 burst；结尾节点必须 newsetup。
3. 每个节点必须填写 what_to_write 和 ends_with。ends_with 必须是可感知画面，不是总结。
4. 禁止使用“本章讲述了、主角经历了、他意识到、这意味着、通过X展现Y、情感升华、不是X而是Y”。
5. 读者期待必须具体，不能只写“期待后续发展”。

幕级节拍：{act_plan}
章节序号：{chapter_index}
章节功能：{chapter_function}
"""
    fallback_reason = ""
    try:
        raw = extract_json_object(llm(prompt, SYSTEM_PROMPT, True))
    except Exception as exc:
        fallback_reason = str(exc)
        raw = _fallback_outline(chapter_index, chapter_function)
    outline = normalize_chapter_outline(raw, chapter_index, chapter_function)
    if fallback_reason:
        outline.setdefault("meta", {})["fallback_reason"] = fallback_reason
    return outline


def normalize_chapter_outline(raw: Any, chapter_index: int, chapter_function: str = "推进本章主线") -> dict[str, Any]:
    if isinstance(raw, list):
        raw = {"nodes": raw}
    if not isinstance(raw, dict):
        raw = _fallback_outline(chapter_index, chapter_function)
    raw_nodes = raw.get("nodes")
    if not isinstance(raw_nodes, list):
        try:
            raw_nodes = extract_json_array(str(raw))
        except Exception:
            raw_nodes = []
    nodes = _normalize_nodes(raw_nodes, chapter_index, chapter_function)
    memo = _normalize_memo(raw.get("memo"), chapter_function)
    emotional_design = _normalize_emotional_design(raw.get("emotional_design"), nodes)
    return {
        "chapter_function": str(raw.get("chapter_function") or chapter_function or "推进本章主线"),
        "narrative_pov": str(raw.get("narrative_pov") or "第三人称有限"),
        "memo": memo,
        "emotional_design": emotional_design,
        "nodes": [node.model_dump() for node in nodes],
        "quality_gates": raw.get("quality_gates") if isinstance(raw.get("quality_gates"), dict) else {},
    }


def _normalize_nodes(raw_nodes: list[Any], chapter_index: int, chapter_function: str) -> list[ChapterNode]:
    nodes_data = [item for item in raw_nodes if isinstance(item, dict)]
    if len(nodes_data) < 5:
        nodes_data = _fallback_nodes(chapter_index, chapter_function)
    nodes_data = nodes_data[:9]
    while len(nodes_data) < 5:
        nodes_data.append(_fallback_nodes(chapter_index, "补足节点")[len(nodes_data)])

    nodes_data[0]["node_type"] = "hook"
    if not any(str(item.get("node_type", "")).lower() == "burst" for item in nodes_data):
        nodes_data[min(4, len(nodes_data) - 2)]["node_type"] = "burst"
    nodes_data[-1]["node_type"] = "newsetup"
    nodes_data[-1].setdefault("segment_function", "emotional_landing")

    nodes: list[ChapterNode] = []
    for idx, item in enumerate(nodes_data, start=1):
        node_type = str(item.get("node_type", "setup")).lower()
        if node_type not in NODE_TYPES:
            node_type = "setup"
        segment_function = str(item.get("segment_function") or _default_segment_function(node_type, idx, len(nodes_data))).lower()
        if segment_function not in SEGMENT_FUNCTIONS:
            segment_function = _default_segment_function(node_type, idx, len(nodes_data))
        expected = int(item.get("expected_word_count", 300) or 300)
        expected = min(max(expected, 200), 500)
        trigger = str(item.get("trigger_point") or f"节点{idx}触发事件")
        what_to_write = str(item.get("what_to_write") or trigger)
        ends_with = str(item.get("ends_with") or _default_ends_with(node_type, idx))
        characters = item.get("characters") if isinstance(item.get("characters"), list) else []
        nodes.append(
            ChapterNode(
                id=str(item.get("id") or uuid.uuid4()),
                chapter_id=str(item.get("chapter_id") or f"chapter-{chapter_index}"),
                index=idx,
                trigger_point=trigger,
                emotion_purpose=str(item.get("emotion_purpose") or "制造期待并推进情绪"),
                reader_expectation=str(item.get("reader_expectation") or "想知道主角如何应对眼前阻碍"),
                node_type=node_type,
                expected_word_count=expected,
                content=item.get("content"),
                segment_function=segment_function,
                what_to_write=what_to_write,
                ends_with=ends_with,
                characters=[str(character) for character in characters if str(character).strip()],
                micro_payoff=str(item.get("micro_payoff") or ""),
            )
        )
    return nodes


def _normalize_memo(raw: Any, chapter_function: str) -> dict[str, Any]:
    memo = raw if isinstance(raw, dict) else {}
    payoff = memo.get("payoff_plan") if isinstance(memo.get("payoff_plan"), dict) else {}
    return {
        "current_task": str(memo.get("current_task") or chapter_function or "推进当前主线任务"),
        "reader_expectation": str(memo.get("reader_expectation") or "读者想看到角色如何处理眼前阻碍，并留下下一步追问。"),
        "payoff_plan": {
            "must_resolve": list(payoff.get("must_resolve") or []),
            "must_hold": list(payoff.get("must_hold") or []),
            "partial_advance": list(payoff.get("partial_advance") or []),
        },
        "downtime_functions": list(memo.get("downtime_functions") or []),
        "key_choices": list(memo.get("key_choices") or []),
        "required_changes": list(memo.get("required_changes") or []),
        "prohibitions": list(memo.get("prohibitions") or []),
    }


def _normalize_emotional_design(raw: Any, nodes: list[ChapterNode]) -> dict[str, Any]:
    design = raw if isinstance(raw, dict) else {}
    moods = design.get("mood_progression") if isinstance(design.get("mood_progression"), list) else []
    return {
        "primary_mood": str(design.get("primary_mood") or "紧张期待"),
        "mood_progression": moods or ["悬念抛出", "压力累积", "留下新期待"],
        "intensity_peak": str(design.get("intensity_peak") or _first_burst(nodes)),
        "emotional_hook": str(design.get("emotional_hook") or nodes[-1].ends_with if nodes else "下一步会发生什么"),
        "intensity_level": min(max(int(design.get("intensity_level") or 6), 1), 10),
        "micro_payoffs": list(design.get("micro_payoffs") or [node.micro_payoff for node in nodes if node.micro_payoff]),
    }


def _default_segment_function(node_type: str, idx: int, total: int) -> str:
    if idx == total:
        return "emotional_landing"
    return {
        "hook": "atmosphere",
        "setup": "character_beat",
        "conflict": "dialogue_push",
        "pressure": "action_beat",
        "burst": "revelation",
        "aftermath": "emotional_landing",
        "harvest": "character_beat",
        "newsetup": "emotional_landing",
    }.get(node_type, "action_beat")


def _default_ends_with(node_type: str, idx: int) -> str:
    if node_type == "newsetup":
        return "一个新的异常细节停在角色眼前，下一步无法回避。"
    if node_type == "burst":
        return "局势第一次向主角倾斜，旁观者的反应凝在现场。"
    return f"节点{idx}结束时，角色面对一个必须立刻处理的新变化。"


def _first_burst(nodes: list[ChapterNode]) -> str:
    for node in nodes:
        if node.node_type == "burst":
            return node.trigger_point
    return nodes[-1].trigger_point if nodes else "情绪峰值场景"


def _fallback_outline(chapter_index: int, chapter_function: str) -> dict[str, Any]:
    nodes = _fallback_nodes(chapter_index, chapter_function)
    return {
        "chapter_function": chapter_function,
        "narrative_pov": "第三人称有限",
        "memo": {},
        "emotional_design": {},
        "nodes": nodes,
    }


def _fallback_nodes(chapter_index: int, chapter_function: str) -> list[dict[str, Any]]:
    return [
        {"index": 1, "node_type": "hook", "segment_function": "atmosphere", "trigger_point": "突发危机或悬念抛出", "emotion_purpose": "立刻抓住读者注意", "reader_expectation": "想知道主角如何应对", "what_to_write": "用一个异常细节打开场面，让主角被迫注意到问题。", "ends_with": "异常细节停在主角眼前。", "expected_word_count": 300},
        {"index": 2, "node_type": "setup", "segment_function": "character_beat", "trigger_point": "补充当前局势与角色目标", "emotion_purpose": "建立期待", "reader_expectation": "期待矛盾升级", "what_to_write": "让角色通过动作和对话确认眼前目标。", "ends_with": "角色把目标落到一个具体行动上。", "expected_word_count": 300},
        {"index": 3, "node_type": "conflict", "segment_function": "dialogue_push", "trigger_point": "反派或阻碍正面出现", "emotion_purpose": "制造紧张", "reader_expectation": "期待主角反击", "what_to_write": "阻碍当场出现，对话里带出代价和限制。", "ends_with": "阻碍压到主角面前，退路变窄。", "expected_word_count": 350},
        {"index": 4, "node_type": "pressure", "segment_function": "action_beat", "trigger_point": "形势继续恶化", "emotion_purpose": "压出憋屈和焦虑", "reader_expectation": "期待底牌", "what_to_write": "让局势进一步失控，主角付出可见代价。", "ends_with": "主角被逼到必须选择的位置。", "expected_word_count": 400},
        {"index": 5, "node_type": "burst", "segment_function": "revelation", "trigger_point": f"围绕{chapter_function}完成爽点爆发", "emotion_purpose": "释放爽感", "reader_expectation": "期待收益和后果", "what_to_write": "主角用前文铺垫的能力、信息或选择完成反击。", "ends_with": "局势第一次向主角倾斜，现场反应凝住。", "micro_payoff": "能力兑现", "expected_word_count": 450},
        {"index": 6, "node_type": "aftermath", "segment_function": "emotional_landing", "trigger_point": "各方反应扩散", "emotion_purpose": "强化满足和震惊", "reader_expectation": "期待收获", "what_to_write": "写出反击后的余波、旁观者反应和主角得到的具体变化。", "ends_with": "一个收获落袋，但新的后果开始显形。", "micro_payoff": "信息兑现", "expected_word_count": 300},
        {"index": 7, "node_type": "newsetup", "segment_function": "emotional_landing", "trigger_point": "新线索或新敌人浮现", "emotion_purpose": "留下追读钩子", "reader_expectation": "期待下一章", "what_to_write": "在余波里露出新的异常、目标或敌意。", "ends_with": "新的异常细节停在角色眼前，下一步无法回避。", "expected_word_count": 300},
    ]
