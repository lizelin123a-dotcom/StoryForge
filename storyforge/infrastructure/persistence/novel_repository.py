from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import uuid4

from storyforge.infrastructure.persistence.database import SessionLocal, init_db
from storyforge.infrastructure.persistence.models.daemon import DaemonStateModel
from storyforge.infrastructure.persistence.models.novel import ChapterModel, EditorChatMessageModel, NodeDraftModel, NovelAssetModel, NovelModel


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
        state = dict(state_row.state) if state_row is not None else None
        chapters = _chapters_for_novel(session, novel_id)
        return _detail_from_model(novel, _merge_chapters_into_state(state, chapters))


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
        state = dict(state_row.state) if state_row is not None else None
        chapters = _chapters_for_novel(session, novel_id)
        return _detail_from_model(novel, _merge_chapters_into_state(state, chapters))


def delete_novel(novel_id: str) -> bool:
    init_db()
    with SessionLocal() as session:
        novel = session.get(NovelModel, novel_id)
        if novel is None:
            return False
        session.query(DaemonStateModel).filter(DaemonStateModel.novel_id == novel_id).delete()
        session.query(ChapterModel).filter(ChapterModel.novel_id == novel_id).delete()
        session.query(NodeDraftModel).filter(NodeDraftModel.novel_id == novel_id).delete()
        session.query(NovelAssetModel).filter(NovelAssetModel.novel_id == novel_id).delete()
        session.query(EditorChatMessageModel).filter(EditorChatMessageModel.novel_id == novel_id).delete()
        session.delete(novel)
        session.commit()
        return True


def save_chapter_text(novel_id: str, chapter_index: int, content: str, title: str | None = None) -> None:
    init_db()
    chapter_id = f"{novel_id}:chapter:{chapter_index}"
    now = datetime.utcnow()
    with SessionLocal() as session:
        chapter = session.get(ChapterModel, chapter_id)
        if chapter is None:
            chapter = ChapterModel(
                id=chapter_id,
                novel_id=novel_id,
                volume_id=None,
                index=chapter_index,
                title=title or f"第 {chapter_index} 章",
                content=content,
                word_count=len(content),
            )
            session.add(chapter)
        else:
            chapter.title = title or chapter.title
            chapter.content = content
            chapter.word_count = len(content)
        novel = session.get(NovelModel, novel_id)
        if novel is not None:
            novel.word_count = sum(row.word_count or 0 for row in session.query(ChapterModel).filter(ChapterModel.novel_id == novel_id).all())
            novel.updated_at = now
        state_row = session.get(DaemonStateModel, novel_id)
        if state_row is not None:
            state = dict(state_row.state or {})
            chapter_texts = list(state.get("chapter_texts") or [])
            while len(chapter_texts) < chapter_index:
                chapter_texts.append("")
            chapter_texts[chapter_index - 1] = content
            state["chapter_texts"] = chapter_texts
            state["baseline_texts"] = chapter_texts
            progress = dict(state.get("progress") or {})
            progress["written_chapters"] = max(int(progress.get("written_chapters") or 0), chapter_index)
            progress["total_words"] = sum(len(str(text or "")) for text in chapter_texts)
            state["progress"] = progress
            state_row.state = state
            state_row.updated_at = now
        session.commit()


def list_node_drafts(novel_id: str, locked_only: bool = False) -> list[dict[str, Any]]:
    init_db()
    with SessionLocal() as session:
        query = session.query(NodeDraftModel).filter(NodeDraftModel.novel_id == novel_id)
        if locked_only:
            query = query.filter(NodeDraftModel.locked == 1)
        rows = query.order_by(NodeDraftModel.chapter_index.asc(), NodeDraftModel.node_index.asc()).all()
        return [_node_draft_from_model(row) for row in rows]


def save_node_draft(novel_id: str, chapter_index: int, node_index: int, node_type: str, content: str, locked: bool = False, source: str = "manual", sync_chapter: bool = False) -> dict[str, Any]:
    init_db()
    draft_id = f"{novel_id}:chapter:{chapter_index}:node:{node_index}"
    now = datetime.utcnow()
    with SessionLocal() as session:
        draft = session.get(NodeDraftModel, draft_id)
        if draft is None:
            draft = NodeDraftModel(id=draft_id, novel_id=novel_id, chapter_index=chapter_index, node_index=node_index, node_type=node_type, content=content, locked=1 if locked else 0, source=source, created_at=now, updated_at=now)
            session.add(draft)
        else:
            draft.node_type = node_type or draft.node_type
            draft.content = content
            draft.locked = 1 if locked else 0
            draft.source = source or draft.source
            draft.updated_at = now
        if sync_chapter:
            _rebuild_chapter_from_nodes(session, novel_id, chapter_index)
        state_row = session.get(DaemonStateModel, novel_id)
        if state_row is not None:
            state = dict(state_row.state or {})
            locked_nodes = [item for item in list_node_drafts(novel_id, locked_only=True) if item.get("id") != draft_id]
            if locked:
                locked_nodes.append(_node_draft_from_model(draft))
            state["locked_nodes"] = locked_nodes
            state_row.state = state
            state_row.updated_at = now
        session.commit()
        session.refresh(draft)
        return _node_draft_from_model(draft)


def list_editor_chat_messages(novel_id: str) -> list[dict[str, Any]]:
    init_db()
    with SessionLocal() as session:
        rows = session.query(EditorChatMessageModel).filter(EditorChatMessageModel.novel_id == novel_id).order_by(EditorChatMessageModel.index.asc()).all()
        return [{"id": row.id, "role": row.role, "content": row.content or "", "index": row.index, "created_at": _format_time(row.created_at)} for row in rows]


def append_editor_chat_messages(novel_id: str, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    init_db()
    now = datetime.utcnow()
    with SessionLocal() as session:
        start = session.query(EditorChatMessageModel).filter(EditorChatMessageModel.novel_id == novel_id).count()
        for offset, message in enumerate(messages):
            role = str(message.get("role") or "user")
            content = str(message.get("content") or "").strip()
            if not content:
                continue
            index = start + offset
            session.add(EditorChatMessageModel(id=f"{novel_id}:chat:{now.timestamp()}:{index}", novel_id=novel_id, index=index, role=role, content=content, created_at=now))
        session.commit()
    return list_editor_chat_messages(novel_id)


def _rebuild_chapter_from_nodes(session: Any, novel_id: str, chapter_index: int) -> None:
    rows = session.query(NodeDraftModel).filter(NodeDraftModel.novel_id == novel_id, NodeDraftModel.chapter_index == chapter_index).order_by(NodeDraftModel.node_index.asc()).all()
    if not rows:
        return
    content = "\n\n".join(row.content or "" for row in rows if row.content)
    if not content:
        return
    chapter_id = f"{novel_id}:chapter:{chapter_index}"
    now = datetime.utcnow()
    chapter = session.get(ChapterModel, chapter_id)
    if chapter is None:
        session.add(ChapterModel(id=chapter_id, novel_id=novel_id, volume_id=None, index=chapter_index, title=f"第 {chapter_index} 章", content=content, word_count=len(content)))
    else:
        chapter.content = content
        chapter.word_count = len(content)
    novel = session.get(NovelModel, novel_id)
    if novel is not None:
        novel.updated_at = now


def upsert_novel_assets(novel_id: str, assets: dict[str, Any]) -> dict[str, str]:
    init_db()
    now = datetime.utcnow()
    with SessionLocal() as session:
        for key, value in assets.items():
            text = str(value or "").strip()
            if not text:
                continue
            asset_id = f"{novel_id}:asset:{key}"
            row = session.get(NovelAssetModel, asset_id)
            if row is None:
                row = NovelAssetModel(id=asset_id, novel_id=novel_id, key=str(key), value=text, created_at=now, updated_at=now)
                session.add(row)
            else:
                row.value = text
                row.updated_at = now
        state_row = session.get(DaemonStateModel, novel_id)
        if state_row is not None:
            state = dict(state_row.state or {})
            state["novel_assets"] = get_novel_assets(novel_id)
            state_row.state = state
            state_row.updated_at = now
        session.commit()
        return get_novel_assets(novel_id)


def get_novel_assets(novel_id: str) -> dict[str, str]:
    init_db()
    with SessionLocal() as session:
        rows = session.query(NovelAssetModel).filter(NovelAssetModel.novel_id == novel_id).order_by(NovelAssetModel.key.asc()).all()
        return {row.key: row.value for row in rows}


def _daemon_states_by_novel_id(session: Any) -> dict[str, dict[str, Any]]:
    rows = session.query(DaemonStateModel).all()
    return {row.novel_id: dict(row.state) for row in rows}


def _chapters_for_novel(session: Any, novel_id: str) -> list[ChapterModel]:
    return session.query(ChapterModel).filter(ChapterModel.novel_id == novel_id).order_by(ChapterModel.index.asc()).all()


def _node_draft_from_model(row: NodeDraftModel) -> dict[str, Any]:
    return {
        "id": row.id,
        "novel_id": row.novel_id,
        "chapter_index": row.chapter_index,
        "node_index": row.node_index,
        "node_type": row.node_type,
        "content": row.content or "",
        "locked": bool(row.locked),
        "source": row.source,
        "updated_at": _format_time(row.updated_at),
    }


def _merge_chapters_into_state(state: dict[str, Any] | None, chapters: list[ChapterModel]) -> dict[str, Any] | None:
    if not chapters:
        return state
    merged = dict(state or {})
    chapter_texts = [chapter.content or "" for chapter in chapters]
    merged["chapter_texts"] = chapter_texts
    merged.setdefault("baseline_texts", chapter_texts)
    progress = dict(merged.get("progress") or {})
    progress["written_chapters"] = len(chapters)
    progress["total_words"] = sum(chapter.word_count or len(chapter.content or "") for chapter in chapters)
    merged["progress"] = progress
    return merged


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
    detail = {
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
    if state and state.get("chapter_texts"):
        detail["chapter_texts"] = state.get("chapter_texts")
    detail["assets"] = get_novel_assets(novel.id)
    detail["node_drafts"] = list_node_drafts(novel.id)
    detail["editor_chat_messages"] = list_editor_chat_messages(novel.id)
    return detail


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
