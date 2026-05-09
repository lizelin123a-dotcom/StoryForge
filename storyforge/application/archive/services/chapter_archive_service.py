from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from storyforge.application.audit.services.chapter_review_service import review_chapter
from storyforge.infrastructure.persistence.database import SessionLocal, init_db
from storyforge.infrastructure.persistence.models.novel_writing import ChapterArchiveModel, CurrentFocusModel
import json

from storyforge.infrastructure.persistence.novel_repository import get_novel_assets, upsert_novel_assets


def archive_chapter(
    *,
    novel_id: str,
    chapter_id: str,
    chapter_index: int,
    chapter_text: str,
    previous_summaries: list[str] | None = None,
    foreshadowing_ledger: dict[str, Any] | None = None,
    review_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Archive a chapter and turn it into durable long-novel memory."""
    init_db()
    review = review_data or review_chapter(
        novel_id=novel_id,
        chapter_index=chapter_index,
        chapter_text=chapter_text,
        previous_summaries=previous_summaries or [],
        foreshadowing_ledger=foreshadowing_ledger or {},
    )
    memory_delta = build_memory_delta(chapter_index=chapter_index, chapter_text=chapter_text, review_data=review)
    current_focus = build_next_focus(chapter_index=chapter_index, review_data=review, memory_delta=memory_delta)
    summary = str(review.get("chapter_summary") or chapter_text[:160]).strip()

    with SessionLocal() as session:
        row = ChapterArchiveModel(
            id=str(uuid4()),
            novel_id=novel_id,
            chapter_id=chapter_id,
            chapter_index=chapter_index,
            summary=summary,
            review_json=review,
            memory_delta_json=memory_delta,
            created_at=datetime.utcnow(),
        )
        session.add(row)
        existing_focus = session.query(CurrentFocusModel).filter(CurrentFocusModel.novel_id == novel_id).first()
        if existing_focus is None:
            session.add(CurrentFocusModel(
                id=str(uuid4()),
                novel_id=novel_id,
                priority=current_focus["priority"],
                active_subplots_json=current_focus["active_subplots"],
                hooks_to_mention_json=current_focus["hooks_to_mention"],
                pacing_intent=current_focus["pacing_intent"],
                constraints_json=current_focus["constraints"],
                updated_at=datetime.utcnow(),
            ))
        else:
            existing_focus.priority = current_focus["priority"]
            existing_focus.active_subplots_json = current_focus["active_subplots"]
            existing_focus.hooks_to_mention_json = current_focus["hooks_to_mention"]
            existing_focus.pacing_intent = current_focus["pacing_intent"]
            existing_focus.constraints_json = current_focus["constraints"]
            existing_focus.updated_at = datetime.utcnow()
        session.commit()

    _upsert_archive_assets(novel_id, memory_delta, current_focus)
    return {
        "status": "archived",
        "chapter_id": chapter_id,
        "chapter_index": chapter_index,
        "summary": summary,
        "review": review,
        "memory_delta": memory_delta,
        "current_focus": current_focus,
        "writer_note": _writer_note(memory_delta, current_focus),
    }


def get_current_focus(novel_id: str) -> dict[str, Any]:
    init_db()
    with SessionLocal() as session:
        row = session.query(CurrentFocusModel).filter(CurrentFocusModel.novel_id == novel_id).first()
        if row is None:
            assets = _decoded_assets(novel_id)
            asset_focus = assets.get("current_focus")
            if isinstance(asset_focus, dict):
                return asset_focus
            return {
                "priority": "先让下一章承接上一章的余波，不急着换线。",
                "active_subplots": [],
                "hooks_to_mention": [],
                "pacing_intent": "承接上一章情绪，并制造新的阅读缺口。",
                "constraints": [],
            }
        return {
            "priority": row.priority,
            "active_subplots": row.active_subplots_json,
            "hooks_to_mention": row.hooks_to_mention_json,
            "pacing_intent": row.pacing_intent,
            "constraints": row.constraints_json,
        }


def build_memory_delta(*, chapter_index: int, chapter_text: str, review_data: dict[str, Any]) -> dict[str, Any]:
    foreshadowing = review_data.get("foreshadowing") if isinstance(review_data.get("foreshadowing"), dict) else {}
    key_events = [str(event) for event in review_data.get("key_events") or [] if str(event).strip()]
    triples = review_data.get("triples") if isinstance(review_data.get("triples"), list) else []
    return {
        "chapter_index": chapter_index,
        "chapter_summary": str(review_data.get("chapter_summary") or chapter_text[:160]).strip(),
        "key_events": key_events[:8],
        "character_triples": triples[:12],
        "new_hooks": foreshadowing.get("new_hooks", []) or [],
        "closed_hooks": foreshadowing.get("closed_hooks", []) or [],
        "still_open_hooks": foreshadowing.get("still_open", []) or [],
        "storyline_progress": str(review_data.get("storyline_progress") or ""),
        "shuang_main": (review_data.get("shuang_analysis") or {}).get("main_type", "") if isinstance(review_data.get("shuang_analysis"), dict) else "",
        "rhythm_pattern": (review_data.get("rhythm") or {}).get("pattern", "") if isinstance(review_data.get("rhythm"), dict) else "",
    }


def build_next_focus(*, chapter_index: int, review_data: dict[str, Any], memory_delta: dict[str, Any]) -> dict[str, Any]:
    open_hooks = memory_delta.get("still_open_hooks") or []
    new_hooks = memory_delta.get("new_hooks") or []
    hooks_to_mention = []
    for hook in [*open_hooks, *new_hooks]:
        if isinstance(hook, dict):
            desc = str(hook.get("description") or "").strip()
            if desc:
                hooks_to_mention.append(desc)
        elif str(hook).strip():
            hooks_to_mention.append(str(hook).strip())
    key_events = memory_delta.get("key_events") or []
    progress = memory_delta.get("storyline_progress") or "上一章事件已经改变局势"
    rhythm = memory_delta.get("rhythm_pattern") or "承接"
    return {
        "priority": f"第 {chapter_index + 1} 章优先承接：{progress}",
        "active_subplots": key_events[:3],
        "hooks_to_mention": hooks_to_mention[:5],
        "pacing_intent": _next_pacing_intent(str(rhythm), bool(hooks_to_mention)),
        "constraints": [
            "不要忘记上一章刚发生的代价和余波。",
            "下一章至少推进一个仍未回收的钩子。" if hooks_to_mention else "下一章需要制造一个新的明确追问。",
            "角色反应必须承接上一章状态，不要像重置了一样。",
        ],
    }


def _next_pacing_intent(rhythm: str, has_hooks: bool) -> str:
    if "不匹配" in rhythm:
        return "先修节奏：减少空转说明，把压力、选择或兑现落到具体场景。"
    if has_hooks:
        return "承接余波，同时推进一个旧钩子，章尾再留下更具体的新问题。"
    return "用一段可见行动承接余波，并在章尾制造新的阅读缺口。"


def _upsert_archive_assets(novel_id: str, memory_delta: dict[str, Any], current_focus: dict[str, Any]) -> None:
    assets = _decoded_assets(novel_id)
    summaries = assets.get("chapter_summaries") if isinstance(assets.get("chapter_summaries"), list) else []
    summaries = [item for item in summaries if not (isinstance(item, dict) and item.get("chapter_index") == memory_delta["chapter_index"])]
    summaries.append({"chapter_index": memory_delta["chapter_index"], "summary": memory_delta["chapter_summary"]})
    hooks = assets.get("hooks") if isinstance(assets.get("hooks"), list) else []
    for hook in memory_delta.get("new_hooks") or []:
        hooks.append(hook)
    upsert_novel_assets(novel_id, {
        "chapter_summaries": json.dumps(summaries, ensure_ascii=False),
        "hooks": json.dumps(hooks, ensure_ascii=False),
        "current_focus": json.dumps(current_focus, ensure_ascii=False),
    })


def _decoded_assets(novel_id: str) -> dict[str, Any]:
    decoded: dict[str, Any] = {}
    for key, value in get_novel_assets(novel_id).items():
        try:
            decoded[key] = json.loads(value)
        except Exception:
            decoded[key] = value
    return decoded


def _writer_note(memory_delta: dict[str, Any], current_focus: dict[str, Any]) -> str:
    parts = [
        f"这一章已经变成长期记忆：{memory_delta.get('chapter_summary', '')}",
        f"下一章优先写：{current_focus.get('priority', '')}",
    ]
    hooks = current_focus.get("hooks_to_mention") or []
    if hooks:
        parts.append("别忘的钩子：" + "；".join(str(hook) for hook in hooks[:3]))
    return "\n".join(part for part in parts if part.strip())
