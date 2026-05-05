from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from storyforge.application.analyst.services.conflict_tracker import track_conflicts
from storyforge.application.analyst.services.information_gap_service import analyze_information_gap
from storyforge.application.analyst.services.rhythm_detector import detect_rhythm_for_texts
from storyforge.application.analyst.services.shuang_point_analyzer import analyze_shuang_points
from storyforge.application.analyst.services.voice_drift_service import detect_voice_drift
from storyforge.application.analyst.services.writing_signal_analyzer import analyze_writing_signals
from storyforge.application.audit.services.chapter_review_service import review_chapter

router = APIRouter(tags=["analyst-audit"])


class TextsRequest(BaseModel):
    texts: list[str] = Field(min_length=1)


class ChapterReviewRequest(BaseModel):
    novel_id: str
    chapter_index: int
    chapter_text: str
    previous_summaries: list[str] = []
    foreshadowing_ledger: dict[str, Any] = {}


class ConflictTrackingRequest(BaseModel):
    novel_id: str
    chapter_index: int
    chapter_text: str
    previous_conflicts: list[dict[str, Any]] = []


class VoiceDriftRequest(BaseModel):
    current_text: str
    baseline_texts: list[str] = []


class WritingSignalRequest(BaseModel):
    text: str = ""


@router.post("/api/v1/analyst/shuang-analysis")
def shuang_analysis(request: TextsRequest) -> dict[str, Any]:
    try:
        return {"results": [analyze_shuang_points(text) for text in request.texts]}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"shuang analysis failed: {exc}") from exc


@router.post("/api/v1/analyst/rhythm")
def rhythm(request: TextsRequest) -> dict[str, Any]:
    try:
        return {"results": detect_rhythm_for_texts(request.texts)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"rhythm detection failed: {exc}") from exc


@router.post("/api/v1/analyst/information-gap")
def information_gap(request: TextsRequest) -> dict[str, Any]:
    try:
        return {"results": [analyze_information_gap(text) for text in request.texts]}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"information gap analysis failed: {exc}") from exc


@router.post("/api/v1/audit/chapter-review")
def chapter_review(request: ChapterReviewRequest) -> dict[str, Any]:
    try:
        return review_chapter(
            novel_id=request.novel_id,
            chapter_index=request.chapter_index,
            chapter_text=request.chapter_text,
            previous_summaries=request.previous_summaries,
            foreshadowing_ledger=request.foreshadowing_ledger,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"chapter review failed: {exc}") from exc


@router.post("/api/v1/analyst/conflict-tracking")
def conflict_tracking(request: ConflictTrackingRequest) -> dict[str, Any]:
    try:
        result = track_conflicts(
            chapter_text=request.chapter_text,
            chapter_index=request.chapter_index,
            previous_conflicts=request.previous_conflicts,
        )
        result["novel_id"] = request.novel_id
        return result
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"conflict tracking failed: {exc}") from exc


@router.post("/api/v1/analyst/voice-drift")
def voice_drift(request: VoiceDriftRequest) -> dict[str, Any]:
    return detect_voice_drift(request.current_text, request.baseline_texts)


@router.post("/api/v1/analyst/writing-signals")
def writing_signals(request: WritingSignalRequest) -> dict[str, Any]:
    return analyze_writing_signals(request.text)
