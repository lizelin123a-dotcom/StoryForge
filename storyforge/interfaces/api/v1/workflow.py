from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from storyforge.application.archive.services.chapter_archive_service import archive_chapter, get_current_focus
from storyforge.application.textops.services.span_mapping_service import apply_span_patch, build_node_spans, list_node_spans

router = APIRouter(tags=["workflow"])


class ArchiveChapterRequest(BaseModel):
    novel_id: str
    chapter_id: str
    chapter_index: int = Field(ge=1)
    chapter_text: str
    previous_summaries: list[str] = []
    foreshadowing_ledger: dict[str, Any] = {}
    review_data: dict[str, Any] | None = None


class BuildSpansRequest(BaseModel):
    novel_id: str
    chapter_id: str
    chapter_text: str
    nodes: list[dict[str, Any]] = []


class SpanPatchRequest(BaseModel):
    text: str
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    content: str


@router.post("/api/v1/workflow/archive-chapter")
def archive_chapter_endpoint(request: ArchiveChapterRequest) -> dict[str, Any]:
    try:
        return archive_chapter(
            novel_id=request.novel_id,
            chapter_id=request.chapter_id,
            chapter_index=request.chapter_index,
            chapter_text=request.chapter_text,
            previous_summaries=request.previous_summaries,
            foreshadowing_ledger=request.foreshadowing_ledger,
            review_data=request.review_data,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"archive chapter failed: {exc}") from exc


@router.get("/api/v1/workflow/{novel_id}/current-focus")
def current_focus_endpoint(novel_id: str) -> dict[str, Any]:
    return get_current_focus(novel_id)


@router.post("/api/v1/workflow/chapter-spans")
def build_spans_endpoint(request: BuildSpansRequest) -> dict[str, Any]:
    try:
        return build_node_spans(
            novel_id=request.novel_id,
            chapter_id=request.chapter_id,
            chapter_text=request.chapter_text,
            nodes=request.nodes,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"build spans failed: {exc}") from exc


@router.get("/api/v1/workflow/{novel_id}/{chapter_id}/chapter-spans")
def list_spans_endpoint(novel_id: str, chapter_id: str) -> dict[str, Any]:
    return list_node_spans(novel_id=novel_id, chapter_id=chapter_id)


@router.post("/api/v1/workflow/span-patch")
def span_patch_endpoint(request: SpanPatchRequest) -> dict[str, Any]:
    if request.end < request.start:
        raise HTTPException(status_code=400, detail="end must be greater than or equal to start")
    return apply_span_patch(text=request.text, start=request.start, end=request.end, content=request.content)
