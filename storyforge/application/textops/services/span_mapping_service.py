from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from storyforge.infrastructure.persistence.database import SessionLocal, init_db
from storyforge.infrastructure.persistence.models.novel_writing import ChapterSpanModel


def build_node_spans(*, novel_id: str, chapter_id: str, chapter_text: str, nodes: list[dict[str, Any]]) -> dict[str, Any]:
    """Create a practical node-to-text map for local rewrite and diagnosis.

    It first tries to find each node draft inside the chapter text. If exact text is not found,
    it falls back to proportional spans based on expected word count.
    """
    init_db()
    normalized_nodes = [node for node in nodes if isinstance(node, dict)]
    spans = _exact_spans(chapter_text, normalized_nodes)
    if len(spans) < len(normalized_nodes):
        spans = _proportional_spans(chapter_text, normalized_nodes)
    now = datetime.utcnow()
    with SessionLocal() as session:
        session.query(ChapterSpanModel).filter(ChapterSpanModel.novel_id == novel_id, ChapterSpanModel.chapter_id == chapter_id).delete()
        for span in spans:
            session.add(ChapterSpanModel(
                id=str(uuid4()),
                novel_id=novel_id,
                chapter_id=chapter_id,
                node_id=span["node_id"],
                start_offset=span["start_offset"],
                end_offset=span["end_offset"],
                outline_snapshot=span.get("outline_snapshot", ""),
                draft_snapshot=span.get("draft_snapshot", ""),
                updated_at=now,
            ))
        session.commit()
    return {"chapter_id": chapter_id, "spans": spans, "writer_note": "正文已经按节点建立定位。以后可以只改某一段，不必整章重写。"}


def list_node_spans(*, novel_id: str, chapter_id: str) -> dict[str, Any]:
    init_db()
    with SessionLocal() as session:
        rows = session.query(ChapterSpanModel).filter(ChapterSpanModel.novel_id == novel_id, ChapterSpanModel.chapter_id == chapter_id).order_by(ChapterSpanModel.start_offset.asc()).all()
        spans = [_span_row(row) for row in rows]
    return {"chapter_id": chapter_id, "spans": spans}


def apply_span_patch(*, text: str, start: int, end: int, content: str) -> dict[str, Any]:
    safe_start = max(0, min(len(text), int(start)))
    safe_end = max(safe_start, min(len(text), int(end)))
    new_text = f"{text[:safe_start]}{content}{text[safe_end:]}"
    return {
        "text": new_text,
        "old_span": {"start": safe_start, "end": safe_end, "content": text[safe_start:safe_end]},
        "new_span": {"start": safe_start, "end": safe_start + len(content), "content": content},
        "writer_note": "这一段已经局部替换，前后正文保留。适合改弱段、补爽点、加强钩子。",
    }


def _exact_spans(chapter_text: str, nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    cursor = 0
    for node in nodes:
        draft = str(node.get("content") or "").strip()
        if not draft:
            continue
        found = chapter_text.find(draft, cursor)
        if found < 0:
            found = chapter_text.find(draft)
        if found < 0:
            continue
        end = found + len(draft)
        spans.append(_span_from_node(node, found, end, draft))
        cursor = end
    return spans


def _proportional_spans(chapter_text: str, nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total_weight = sum(max(1, int(node.get("expected_word_count") or node.get("target_words") or 300)) for node in nodes) or len(nodes) or 1
    spans: list[dict[str, Any]] = []
    cursor = 0
    text_len = len(chapter_text)
    for index, node in enumerate(nodes):
        weight = max(1, int(node.get("expected_word_count") or node.get("target_words") or 300))
        if index == len(nodes) - 1:
            end = text_len
        else:
            rough_end = cursor + int(text_len * weight / total_weight)
            end = _nearest_sentence_boundary(chapter_text, rough_end, cursor)
        draft = chapter_text[cursor:end]
        spans.append(_span_from_node(node, cursor, end, draft))
        cursor = end
    return spans


def _nearest_sentence_boundary(text: str, rough: int, minimum: int) -> int:
    candidates = [pos for pos in range(max(minimum + 1, rough - 80), min(len(text), rough + 80)) if text[pos:pos + 1] in "。！？\n"]
    if not candidates:
        return max(minimum, min(len(text), rough))
    return min(candidates, key=lambda pos: abs(pos - rough)) + 1


def _span_from_node(node: dict[str, Any], start: int, end: int, draft: str) -> dict[str, Any]:
    outline = " / ".join(str(node.get(key) or "") for key in ["node_type", "trigger_point", "reader_expectation", "ends_with"] if str(node.get(key) or "").strip())
    return {
        "node_id": str(node.get("id") or f"node-{node.get('index', len(draft))}"),
        "node_index": int(node.get("index") or node.get("node_index") or 0),
        "start_offset": start,
        "end_offset": end,
        "outline_snapshot": outline,
        "draft_snapshot": draft[:1200],
    }


def _span_row(row: ChapterSpanModel) -> dict[str, Any]:
    return {
        "id": row.id,
        "node_id": row.node_id,
        "start_offset": row.start_offset,
        "end_offset": row.end_offset,
        "outline_snapshot": row.outline_snapshot,
        "draft_snapshot": row.draft_snapshot,
        "updated_at": row.updated_at.isoformat() if row.updated_at else "",
    }
