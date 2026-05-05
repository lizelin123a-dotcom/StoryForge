from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from storyforge.infrastructure.knowledge import select_writing_guidance


@dataclass(frozen=True)
class ContextEntry:
    source: str
    title: str
    content: Any
    priority: int = 0


@dataclass(frozen=True)
class ContextPackage:
    chapter_index: int
    selected_context: list[ContextEntry] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    hook_agenda: list[dict[str, Any]] = field(default_factory=list)
    memory_brief: str = ""

    def to_prompt_dict(self) -> dict[str, Any]:
        return {
            "chapter_index": self.chapter_index,
            "selected_context": [entry.__dict__ for entry in self.selected_context],
            "constraints": self.constraints,
            "hook_agenda": self.hook_agenda,
            "memory_brief": self.memory_brief,
        }


def build_governed_context(
    *,
    chapter_index: int,
    story_bible: dict[str, Any],
    chapter_summaries: list[str],
    baseline_texts: list[str],
    foreshadowing_ledger: dict[str, Any],
    manual_instructions: str = "",
    novel_assets: dict[str, Any] | None = None,
    locked_nodes: list[dict[str, Any]] | None = None,
    max_summaries: int = 5,
    max_baselines: int = 3,
) -> dict[str, Any]:
    """Build a compact governed working context instead of dumping all state into prompts."""
    recent_summaries = [text for text in chapter_summaries[-max_summaries:] if text]
    recent_baselines = [text for text in baseline_texts[-max_baselines:] if text]
    active_hooks = _select_active_hooks(foreshadowing_ledger, chapter_index)
    writing_guidance = select_writing_guidance("结构", "期待感", "爽点", "角色", "冲突", limit=4)
    assets = novel_assets or {}
    locked = _select_locked_nodes(locked_nodes or [], chapter_index)
    entries = [
        ContextEntry("story_bible", "故事圣经", story_bible, 100),
        ContextEntry("novel_assets", "共创资产", assets, 98),
        ContextEntry("locked_nodes", "已锁定节点", locked, 97),
        ContextEntry("writing_guidance", "写作教学规则", writing_guidance, 95),
        ContextEntry("chapter_summaries", "近章摘要", recent_summaries, 80),
        ContextEntry("baseline_texts", "近章文风样本", recent_baselines, 60),
        ContextEntry("foreshadowing", "可用伏笔", active_hooks, 70),
    ]
    constraints = [
        "只使用 selected_context 中与当前节点相关的信息，避免把长期设定一次性灌入正文。",
        "优先延续近三章的叙事视角、节奏和角色状态。",
        "伏笔只推进或回收 hook_agenda 中的条目，不随意新增无关大坑。",
        "优先遵循 writing_guidance 中的写作教学规则：期待感、爽点、结构、冲突和角色行动必须落到具体剧情。",
        "novel_assets 是作者在共创阶段确认的作品骨架，优先级高于临时生成想法。",
        "locked_nodes 是作者人工确认或锁定的节点，后续生成必须承接，不得覆盖、否定或重写。"
    ]
    if manual_instructions.strip():
        constraints.append(f"人工审阅指令优先：{manual_instructions.strip()}")
    package = ContextPackage(
        chapter_index=chapter_index,
        selected_context=entries,
        constraints=constraints,
        hook_agenda=active_hooks,
        memory_brief=_build_memory_brief(recent_summaries, active_hooks),
    )
    return {
        "story_bible": story_bible,
        "history_summaries": recent_summaries,
        "baseline_texts": recent_baselines,
        "manual_instructions": manual_instructions,
        "context_package": package.to_prompt_dict(),
        "selected_context": [entry.__dict__ for entry in entries],
        "hook_agenda": active_hooks,
        "constraints": constraints,
        "writing_guidance": writing_guidance,
        "novel_assets": assets,
        "locked_nodes": locked,
    }


def apply_review_delta(state: dict[str, Any], chapter_index: int, review_data: dict[str, Any], chapter_text: str) -> dict[str, Any]:
    """Apply review output as a runtime-state delta and keep compact memory records."""
    runtime_memory = state.setdefault("runtime_memory", {"chapter_summaries": [], "hooks": [], "facts": []})
    summary = str(review_data.get("chapter_summary") or chapter_text[:120]).strip()
    if summary:
        _upsert_by_key(runtime_memory.setdefault("chapter_summaries", []), "chapter_index", {"chapter_index": chapter_index, "summary": summary})

    for event in review_data.get("key_events") or []:
        text = str(event).strip()
        if text:
            runtime_memory.setdefault("facts", []).append({"chapter_index": chapter_index, "type": "key_event", "text": text})

    foreshadowing = review_data.get("foreshadowing", {}) if isinstance(review_data.get("foreshadowing", {}), dict) else {}
    hooks = runtime_memory.setdefault("hooks", [])
    for hook in foreshadowing.get("new_hooks", []) or []:
        if isinstance(hook, dict):
            _upsert_by_key(hooks, "description", {**hook, "status": "open", "origin_chapter": chapter_index})
    for hook in foreshadowing.get("closed_hooks", []) or []:
        if isinstance(hook, dict):
            description = str(hook.get("description") or "").strip()
            if not description:
                continue
            existing = next((item for item in hooks if item.get("description") == description), None)
            if existing:
                existing.update({"status": "closed", "closed_chapter": chapter_index})
            else:
                hooks.append({**hook, "status": "closed", "closed_chapter": chapter_index})

    state.setdefault("runtime_state_deltas", []).append({
        "chapter_index": chapter_index,
        "summary": summary,
        "new_hooks": foreshadowing.get("new_hooks", []) or [],
        "closed_hooks": foreshadowing.get("closed_hooks", []) or [],
    })
    state["hook_health_records"] = evaluate_hook_health(state.get("foreshadowing_ledger", {}), chapter_index)
    return state


def evaluate_hook_health(foreshadowing_ledger: dict[str, Any], chapter_index: int) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for hook in foreshadowing_ledger.get("still_open", []) or []:
        if not isinstance(hook, dict):
            continue
        age = int(hook.get("age_chapters") or max(0, chapter_index - int(hook.get("origin_chapter", chapter_index) or chapter_index)))
        if age >= 8:
            issues.append({"severity": "warning", "description": str(hook.get("description", "未命名伏笔")), "suggestion": "该伏笔悬挂过久，建议在后续 1-3 章推进或回收。"})
    return issues


def _select_locked_nodes(nodes: list[dict[str, Any]], chapter_index: int, limit: int = 8) -> list[dict[str, Any]]:
    selected = []
    for node in nodes:
        if not isinstance(node, dict) or not node.get("locked"):
            continue
        node_chapter = int(node.get("chapter_index") or 0)
        if node_chapter <= chapter_index:
            selected.append({
                "chapter_index": node_chapter,
                "node_index": int(node.get("node_index") or 0),
                "node_type": str(node.get("node_type") or ""),
                "content": str(node.get("content") or "")[:900],
                "source": str(node.get("source") or "manual"),
            })
    return sorted(selected, key=lambda item: (item["chapter_index"], item["node_index"]), reverse=True)[:limit]


def _select_active_hooks(ledger: dict[str, Any], chapter_index: int, limit: int = 6) -> list[dict[str, Any]]:
    hooks: list[dict[str, Any]] = []
    for hook in ledger.get("still_open", []) or []:
        if isinstance(hook, dict):
            age = int(hook.get("age_chapters") or 0)
            expected = int(hook.get("expected_closure_chapter") or chapter_index + 99)
            priority = age + (5 if expected <= chapter_index + 2 else 0)
            hooks.append({**hook, "priority": priority})
    return sorted(hooks, key=lambda item: int(item.get("priority") or 0), reverse=True)[:limit]


def _build_memory_brief(summaries: list[str], hooks: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    if summaries:
        parts.append("近章走势：" + "；".join(summaries[-3:]))
    if hooks:
        parts.append("当前伏笔：" + "；".join(str(hook.get("description") or hook) for hook in hooks[:3]))
    return "\n".join(parts)


def _upsert_by_key(rows: list[dict[str, Any]], key: str, row: dict[str, Any]) -> None:
    value = row.get(key)
    for existing in rows:
        if existing.get(key) == value:
            existing.update(row)
            return
    rows.append(row)
