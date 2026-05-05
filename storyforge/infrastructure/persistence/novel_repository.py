from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import uuid4

from storyforge.infrastructure.persistence.database import SessionLocal, init_db
from storyforge.infrastructure.persistence.models.daemon import DaemonStateModel
from storyforge.infrastructure.persistence.models.novel import NovelModel


STATUS_LABELS = {
    "idle": "未开始",
    "running": "写作中",
    "paused": "已暂停",
    "completed": "已完成",
    "error": "错误",
}


def create_novel(
    title: str,
    world_setting: str,
    characters: list[dict[str, Any]] | str,
    genre: str,
    target_word_count: int,
) -> dict[str, Any]:
    init_db()
    now = datetime.utcnow()
    normalized_world = world_setting.strip()
    novel = NovelModel(
        id=str(uuid4()),
        title=title.strip(),
        author="StoryForge",
        genre=genre.strip(),
        summary=normalized_world[:240],
        world_setting=normalized_world,
        characters=_characters_to_json(characters),
        target_word_count=max(1, int(target_word_count or 120000)),
        status="idle",
        word_count=0,
        created_at=now,
        updated_at=now,
    )
    with SessionLocal() as session:
        session.add(novel)
        session.commit()
        session.refresh(novel)
        return _detail_from_model(novel)


def list_novels() -> list[dict[str, Any]]:
    init_db()
    with SessionLocal() as session:
        rows = session.query(NovelModel).order_by(NovelModel.updated_at.desc()).all()
        states = _daemon_states_by_novel_id(session)
        return [_summary_from_model(row, states.get(row.id)) for row in rows]


def get_novel(novel_id: str) -> dict[str, Any] | None:
    init_db()
    with SessionLocal() as session:
        novel = session.get(NovelModel, novel_id)
        if novel is None:
            return None
        state_row = session.get(DaemonStateModel, novel_id)
        return _detail_from_model(novel, dict(state_row.state) if state_row is not None else None)


def update_target_word_count(novel_id: str, target_word_count: int | None) -> dict[str, Any] | None:
    init_db()
    with SessionLocal() as session:
        novel = session.get(NovelModel, novel_id)
        if novel is None:
            return None
        if target_word_count:
            novel.target_word_count = max(1, int(target_word_count))
        novel.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(novel)
        state_row = session.get(DaemonStateModel, novel_id)
        return _detail_from_model(novel, dict(state_row.state) if state_row is not None else None)


def delete_novel(novel_id: str) -> bool:
    init_db()
    with SessionLocal() as session:
        novel = session.get(NovelModel, novel_id)
        if novel is None:
            return False
        session.query(DaemonStateModel).filter(DaemonStateModel.novel_id == novel_id).delete()
        session.delete(novel)
        session.commit()
        return True


def _daemon_states_by_novel_id(session: Any) -> dict[str, dict[str, Any]]:
    rows = session.query(DaemonStateModel).all()
    return {row.novel_id: dict(row.state) for row in rows}


def _summary_from_model(novel: NovelModel, state: dict[str, Any] | None = None) -> dict[str, Any]:
    status = _state_status(novel, state)
    word_count = _state_word_count(novel, state)
    return {
        "id": novel.id,
        "title": novel.title,
        "genre": novel.genre,
        "status": STATUS_LABELS.get(status, status),
        "raw_status": status,
        "words": word_count,
        "word_count": word_count,
        "target_word_count": _state_target_words(novel, state),
        "updated_at": _format_time(_state_updated_at(novel, state)),
    }


def _detail_from_model(novel: NovelModel, state: dict[str, Any] | None = None) -> dict[str, Any]:
    status = _state_status(novel, state)
    word_count = _state_word_count(novel, state)
    return {
        "id": novel.id,
        "title": novel.title,
        "author": getattr(novel, "author", "StoryForge"),
        "genre": novel.genre,
        "summary": getattr(novel, "summary", "") or "",
        "world_setting": getattr(novel, "world_setting", None) or getattr(novel, "summary", "") or "",
        "characters": _characters_from_json(getattr(novel, "characters", "[]")),
        "target_word_count": _state_target_words(novel, state),
        "status": status,
        "status_label": STATUS_LABELS.get(status, status),
        "word_count": word_count,
        "words": word_count,
        "created_at": _format_time(getattr(novel, "created_at", None)),
        "updated_at": _format_time(_state_updated_at(novel, state)),
    }


def _state_status(novel: NovelModel, state: dict[str, Any] | None) -> str:
    if state and state.get("status"):
        return str(state.get("status"))
    return str(getattr(novel, "status", "idle") or "idle")


def _state_word_count(novel: NovelModel, state: dict[str, Any] | None) -> int:
    progress = state.get("progress") if state else None
    if isinstance(progress, dict):
        return int(progress.get("total_words") or 0)
    return int(getattr(novel, "word_count", 0) or 0)


def _state_target_words(novel: NovelModel, state: dict[str, Any] | None) -> int:
    progress = state.get("progress") if state else None
    if isinstance(progress, dict) and progress.get("target_words"):
        return int(progress.get("target_words") or 120000)
    return int(getattr(novel, "target_word_count", 120000) or 120000)


def _state_updated_at(novel: NovelModel, state: dict[str, Any] | None) -> datetime | None:
    if state and state.get("updated_at"):
        try:
            return datetime.fromisoformat(str(state["updated_at"]))
        except ValueError:
            pass
    return getattr(novel, "updated_at", None) or getattr(novel, "created_at", None)


def _characters_to_json(characters: list[dict[str, Any]] | str) -> str:
    if isinstance(characters, str):
        return characters
    return json.dumps(characters, ensure_ascii=False)


def _characters_from_json(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if not value:
        return []
    try:
        data = json.loads(str(value))
        return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []
    except Exception:
        return [{"name": "角色设定", "role": "设定", "description": str(value)}]


def _format_time(value: datetime | None) -> str:
    if not value:
        return ""
    return value.strftime("%Y-%m-%d %H:%M")
