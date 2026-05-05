from __future__ import annotations

from typing import Any

from storyforge.infrastructure.ai.openai_adapter import call_llm
from storyforge.infrastructure.knowledge import select_writing_guidance

STAGE_FIELDS = [
    ("核心灵感", "用一句话确认这部小说真正想写的快感和承诺。"),
    ("主角欲望", "主角长期想要什么，眼前第一步想拿到什么。"),
    ("世界规则", "世界如何运转，哪些规则会制造爽点和限制。"),
    ("核心矛盾", "谁阻碍主角，阻碍背后的利益与代价是什么。"),
    ("期待钩子", "读者为什么愿意继续看下一章。"),
    ("爽点模型", "主角如何获得优势、反击、揭示底牌或满足情绪缺口。"),
    ("角色关系", "主角、对手、盟友之间的情绪关系和行动关系。"),
]


def next_cocreation_turn(*, logline: str, messages: list[dict[str, str]], assets: dict[str, Any], api_key: str = "", api_base_url: str = "", model: str = "") -> dict[str, Any]:
    missing = [name for name, _desc in STAGE_FIELDS if not str(assets.get(name, "")).strip()]
    current = missing[0] if missing else "写作入口"
    guidance = select_writing_guidance(current, "期待感", "爽点", "结构", limit=2, max_chars=900)
    user_last = _last_user_message(messages) or logline
    prompt = f"""你是 StoryForge 的共创编辑。不要一次性替作者生成完整设定，而是像对话框一样逐步追问、归纳和沉淀小说资产。

原始灵感：{logline}
当前已确认资产：{assets}
本轮用户输入：{user_last}
当前优先补全字段：{current}
可参考写作教学规则：{guidance}

请返回 JSON：
{{
  "reply": "给作者的自然对话回复，先简短归纳，再只问1-2个关键问题",
  "asset_patch": {{"字段名": "从本轮输入中能确认的内容"}},
  "next_focus": "下一轮重点",
  "ready_for_writing": false
}}

要求：
1. 不要替作者拍板大量内容。
2. 能从用户话里确认的资产才写入 asset_patch。
3. 如果七个字段已经基本完整，ready_for_writing 可以为 true。
4. 语言像专业网文编辑，不要像表格填报。"""
    try:
        content = call_llm(prompt=prompt, system_prompt="你只返回 JSON。", json_mode=True, api_key=api_key or None, base_url=(api_base_url or None), model=model or None)
        import json
        data = json.loads(content)
    except Exception:
        data = _local_turn(logline=logline, assets=assets, current=current, user_last=user_last)
    return _normalize_turn(data, current)


def _local_turn(*, logline: str, assets: dict[str, Any], current: str, user_last: str) -> dict[str, Any]:
    patch = {}
    if user_last and current != "写作入口":
        patch[current] = user_last[:500]
    question = next((desc for name, desc in STAGE_FIELDS if name == current), "现在可以把这些资产转入节点写作。")
    return {
        "reply": f"我先把这一轮理解为“{current}”方向。{question} 你可以继续补一句：这件事最吸引读者的地方是什么？",
        "asset_patch": patch,
        "next_focus": current,
        "ready_for_writing": current == "写作入口",
    }


def _normalize_turn(data: dict[str, Any], current: str) -> dict[str, Any]:
    patch = data.get("asset_patch") if isinstance(data.get("asset_patch"), dict) else {}
    return {
        "reply": str(data.get("reply") or "我收到这个想法了，我们继续把它拆成可写的小说资产。"),
        "asset_patch": {str(k): str(v) for k, v in patch.items() if str(v).strip()},
        "next_focus": str(data.get("next_focus") or current),
        "ready_for_writing": bool(data.get("ready_for_writing")),
        "fields": [{"name": name, "description": desc} for name, desc in STAGE_FIELDS],
    }


def _last_user_message(messages: list[dict[str, str]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return str(message.get("content") or "")
    return ""
