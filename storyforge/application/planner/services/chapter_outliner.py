import uuid
from typing import Any, Callable

from storyforge.application.dissect.services.common import extract_json_array
from storyforge.domain.node.node import ChapterNode
from storyforge.infrastructure.ai.openai_adapter import call_llm

LLMCaller = Callable[[str, str, bool], str]

NODE_TYPES = {"hook", "setup", "conflict", "pressure", "burst", "aftermath", "harvest", "newsetup"}
SYSTEM_PROMPT = """你是节点级章纲规划专家。
每章必须 5-9 个节点，每节点 200-500 字；第一个节点 hook，至少一个 burst，最后一个 newsetup。
节点类型只能是 hook/setup/conflict/pressure/burst/aftermath/harvest/newsetup。
必须输出 JSON object 或 JSON array。
"""


def generate_chapter_outline(
    act_plan: dict[str, Any],
    chapter_index: int,
    chapter_function: str,
    llm: LLMCaller = call_llm,
) -> list[ChapterNode]:
    prompt = f"""请为指定章节生成节点级章纲。
流程：
1. 判断该章在幕中的位置和功能。
2. 选择节点类型模板：开场章偏 hook+setup，高潮章偏 pressure+burst。
3. 生成 5-9 个节点。
4. 开篇第一节点必须 hook；整章至少一个 burst；结尾节点必须 newsetup。
输出 JSON：{{"nodes": [{{"index": 1, "node_type": "hook", "trigger_point": "触发点", "emotion_purpose": "情绪目的", "reader_expectation": "读者期待", "expected_word_count": 300}}]}}
幕级节拍：{act_plan}
章节序号：{chapter_index}
章节功能：{chapter_function}
"""
    try:
        raw_nodes = extract_json_array(llm(prompt, SYSTEM_PROMPT, True))
    except Exception:
        raw_nodes = _fallback_nodes(chapter_index, chapter_function)
    return _normalize_nodes(raw_nodes, chapter_index)


def _normalize_nodes(raw_nodes: list[Any], chapter_index: int) -> list[ChapterNode]:
    nodes_data = [item for item in raw_nodes if isinstance(item, dict)]
    if len(nodes_data) < 5:
        nodes_data = _fallback_nodes(chapter_index, "推进本章主线")
    nodes_data = nodes_data[:9]
    while len(nodes_data) < 5:
        nodes_data.append(_fallback_nodes(chapter_index, "补足节点")[len(nodes_data)])

    nodes_data[0]["node_type"] = "hook"
    if not any(str(item.get("node_type", "")).lower() == "burst" for item in nodes_data):
        nodes_data[min(4, len(nodes_data) - 2)]["node_type"] = "burst"
    nodes_data[-1]["node_type"] = "newsetup"

    nodes: list[ChapterNode] = []
    for idx, item in enumerate(nodes_data, start=1):
        node_type = str(item.get("node_type", "setup")).lower()
        if node_type not in NODE_TYPES:
            node_type = "setup"
        expected = int(item.get("expected_word_count", 300) or 300)
        expected = min(max(expected, 200), 500)
        nodes.append(
            ChapterNode(
                id=str(uuid.uuid4()),
                chapter_id=f"chapter-{chapter_index}",
                index=idx,
                trigger_point=str(item.get("trigger_point") or f"节点{idx}触发事件"),
                emotion_purpose=str(item.get("emotion_purpose") or "制造期待并推进情绪"),
                reader_expectation=str(item.get("reader_expectation") or "期待主角破局"),
                node_type=node_type,
                expected_word_count=expected,
                content=item.get("content"),
            )
        )
    return nodes


def _fallback_nodes(chapter_index: int, chapter_function: str) -> list[dict[str, Any]]:
    return [
        {"index": 1, "node_type": "hook", "trigger_point": "突发危机或悬念抛出", "emotion_purpose": "立刻抓住读者注意", "reader_expectation": "想知道主角如何应对", "expected_word_count": 300},
        {"index": 2, "node_type": "setup", "trigger_point": "补充当前局势与角色目标", "emotion_purpose": "建立期待", "reader_expectation": "期待矛盾升级", "expected_word_count": 300},
        {"index": 3, "node_type": "conflict", "trigger_point": "反派或阻碍正面出现", "emotion_purpose": "制造紧张", "reader_expectation": "期待主角反击", "expected_word_count": 350},
        {"index": 4, "node_type": "pressure", "trigger_point": "形势继续恶化", "emotion_purpose": "压出憋屈和焦虑", "reader_expectation": "期待底牌", "expected_word_count": 400},
        {"index": 5, "node_type": "burst", "trigger_point": f"围绕{chapter_function}完成爽点爆发", "emotion_purpose": "释放爽感", "reader_expectation": "期待收益和后果", "expected_word_count": 450},
        {"index": 6, "node_type": "aftermath", "trigger_point": "各方反应扩散", "emotion_purpose": "强化满足和震惊", "reader_expectation": "期待收获", "expected_word_count": 300},
        {"index": 7, "node_type": "newsetup", "trigger_point": "新线索或新敌人浮现", "emotion_purpose": "留下追读钩子", "reader_expectation": "期待下一章", "expected_word_count": 300},
    ]
