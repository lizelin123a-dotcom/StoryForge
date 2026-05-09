from __future__ import annotations

from typing import Any

from storyforge.infrastructure.ai.openai_adapter import call_llm
from storyforge.infrastructure.knowledge import get_editor_skills, select_writing_guidance

STAGE_FIELDS = [
    ("核心灵感", "用一句话确认这部小说真正想写的快感和承诺。"),
    ("主角欲望", "主角长期想要什么，眼前第一步想拿到什么。"),
    ("世界规则", "世界如何运转，哪些规则会制造爽点和限制。"),
    ("核心矛盾", "谁阻碍主角，阻碍背后的利益与代价是什么。"),
    ("期待钩子", "读者为什么愿意继续看下一章。"),
    ("爽点模型", "主角如何获得优势、反击、揭示底牌或满足情绪缺口。"),
    ("角色关系", "主角、对手、盟友之间的情绪关系和行动关系。"),
]


def next_cocreation_turn(*, logline: str, messages: list[dict[str, str]], assets: dict[str, Any], writing_context: dict[str, Any] | None = None, skill_ids: list[str] | None = None, api_key: str = "", api_base_url: str = "", model: str = "") -> dict[str, Any]:
    missing = [name for name, _desc in STAGE_FIELDS if not str(assets.get(name, "")).strip()]
    current = missing[0] if missing else "写作入口"
    guidance = select_writing_guidance(current, "期待感", "爽点", "结构", limit=2, max_chars=900)
    editor_skills = get_editor_skills(skill_ids or [], max_chars=3600)
    user_last = _last_user_message(messages) or logline
    prompt = f"""你是 StoryForge 的共创编辑。不要一次性替作者生成完整设定，而是像对话框一样逐步追问、归纳、修正和沉淀小说资产。

原始灵感：{logline}
当前已确认资产：{assets}
本轮用户输入：{user_last}
当前优先补全字段：{current}
当前写作现场：{writing_context or {}}
已启用编辑 Skill：{editor_skills}
可参考写作教学规则：{guidance}

请返回 JSON：
{{
  "reply": "给作者的自然对话回复，先简短归纳，再只问1-2个关键问题",
  "asset_patch": {{"字段名": "从本轮输入中能确认的内容"}},
  "edit_patch": {{
    "target": "node 或 chapter 或 span 或 none",
    "mode": "replace 或 append 或 insert 或 none",
    "content": "如果作者要求改稿，给出可直接应用到当前节点/章节/选中段落的文本；否则为空",
    "reason": "为什么这样改",
    "lock_node": false,
    "span": {{"start": 0, "end": 0}}
  }},
  "ui_actions": [
    {{
      "type": "rewrite_node 或 apply_edit_patch 或 rewrite_chapter 或 update_chapter_outline 或 update_book_outline 或 update_asset 或 delete_asset 或 clear_assets",
      "label": "给作者看的操作名",
      "target": {{"key": "案头设定名，可选"}},
      "payload": {{"content": "新内容，可选"}},
      "risk": "low 或 medium 或 high",
      "preview": "这次操作会改变什么"
    }}
  ],
  "next_focus": "下一轮重点",
  "ready_for_writing": false
}}

要求：
1. 不要替作者拍板大量内容。
2. 能从用户话里确认的资产才写入 asset_patch。asset_patch 既可以补空字段，也可以覆盖已有字段；如果用户后续思路改变、否定、扩展或重构了前面资产，必须写入新的字段值来修正旧资产。
2.5 如果 writing_context 有当前章节、当前节点、检测结果，请优先针对作者正在写的文本给建议。
2.6 如果作者明确要求“改一下/替换/补一段/写入/应用/加强爽点/加钩子”等，必须给 edit_patch。若用户说“这一段/这段/选中部分”，target=span；否则 target 优先 node，其次 chapter。不要只给建议。
3. 如果七个字段已经基本完整，ready_for_writing 可以为 true。
4. 语言像专业网文编辑，不要像表格填报。
5. 已启用编辑 Skill 的规则优先级高于普通建议，必须体现在判断、追问和 edit_patch 中。
6. 如果作者要求操控界面，例如重写当前小节、写入当前小节、重写本章、修改/删除/清空案头设定，必须生成 ui_actions。禁止生成任何修改模型配置、API Key、Base URL、模型名的 ui_actions。
7. 删除或清空类操作 risk 必须为 high。
8. 只要用户提到“章纲、节点安排、小节目标、本章结构”，必须生成 update_chapter_outline，不要生成 target=chapter 的 edit_patch；target=chapter 只代表正文。
9. 只要用户提到“大纲、全书大纲、分卷、主线规划”，必须生成 update_book_outline，不要写入正文。"""
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
        "reply": f"我先把这一轮理解为“{current}”方向。{question} 如果这会改变前面已经确认的资产，我会直接把旧资产修正掉。",
        "asset_patch": patch,
        "next_focus": current,
        "ready_for_writing": current == "写作入口",
        "edit_patch": _local_edit_patch(user_last),
        "ui_actions": _local_ui_actions(user_last),
    }


def _normalize_turn(data: dict[str, Any], current: str) -> dict[str, Any]:
    patch = data.get("asset_patch") if isinstance(data.get("asset_patch"), dict) else {}
    edit_patch = data.get("edit_patch") if isinstance(data.get("edit_patch"), dict) else {}
    target = str(edit_patch.get("target") or "none")
    mode = str(edit_patch.get("mode") or "none")
    content = str(edit_patch.get("content") or "")
    if target not in {"node", "chapter", "span", "none"}:
        target = "none"
    if mode not in {"replace", "append", "insert", "none"}:
        mode = "none"
    if not content.strip():
        target = "none"
        mode = "none"
    span = edit_patch.get("span") if isinstance(edit_patch.get("span"), dict) else {}
    return {
        "reply": str(data.get("reply") or "我收到这个想法了，我们继续把它拆成可写的小说资产。"),
        "asset_patch": {str(k): str(v) for k, v in patch.items() if str(v).strip()},
        "edit_patch": {"target": target, "mode": mode, "content": content, "reason": str(edit_patch.get("reason") or ""), "lock_node": bool(edit_patch.get("lock_node")), "span": {"start": int(span.get("start") or 0), "end": int(span.get("end") or 0)}},
        "ui_actions": _normalize_ui_actions(data.get("ui_actions")),
        "next_focus": str(data.get("next_focus") or current),
        "ready_for_writing": bool(data.get("ready_for_writing")),
        "fields": [{"name": name, "description": desc} for name, desc in STAGE_FIELDS],
    }


def _normalize_ui_actions(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    allowed = {"rewrite_node", "apply_edit_patch", "rewrite_chapter", "update_chapter_outline", "update_book_outline", "update_asset", "delete_asset", "clear_assets"}
    blocked_words = ("api", "key", "base", "url", "模型配置", "模型名", "model", "DeepSeek Key", "Base URL")
    actions: list[dict[str, Any]] = []
    for item in value[:5]:
        if not isinstance(item, dict):
            continue
        action_type = str(item.get("type") or "")
        label = str(item.get("label") or action_type)
        preview = str(item.get("preview") or "")
        if action_type not in allowed:
            continue
        text_blob = f"{label} {preview} {item.get('target') or ''} {item.get('payload') or ''}"
        if any(word.lower() in text_blob.lower() for word in blocked_words):
            continue
        target = item.get("target") if isinstance(item.get("target"), dict) else {}
        payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
        risk = str(item.get("risk") or "medium")
        if action_type in {"delete_asset", "clear_assets", "rewrite_chapter", "update_book_outline"}:
            risk = "high"
        if risk not in {"low", "medium", "high"}:
            risk = "medium"
        actions.append({"type": action_type, "label": label, "target": target, "payload": payload, "risk": risk, "preview": preview})
    return actions


def _local_ui_actions(user_last: str) -> list[dict[str, Any]]:
    if "重写本章" in user_last:
        return [{"type": "rewrite_chapter", "label": "重写本章", "target": {}, "payload": {}, "risk": "high", "preview": "清空本章并从第 1 节重新生成。"}]
    if "清空" in user_last and "设定" in user_last:
        return [{"type": "clear_assets", "label": "清空案头设定", "target": {}, "payload": {}, "risk": "high", "preview": "删除当前作品的案头设定。"}]
    return []


def _local_edit_patch(user_last: str) -> dict[str, Any]:
    if not any(word in user_last for word in ("改", "补", "写入", "应用", "替换", "加强", "加钩子", "爽点")):
        return {"target": "none", "mode": "none", "content": "", "reason": "", "lock_node": False, "span": {"start": 0, "end": 0}}
    return {
        "target": "node",
        "mode": "append",
        "content": f"【人工思路补写】{user_last}",
        "reason": "本地规则判断用户希望把当前想法写入正在处理的节点。",
        "lock_node": False,
        "span": {"start": 0, "end": 0},
    }


def _last_user_message(messages: list[dict[str, str]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return str(message.get("content") or "")
    return ""
