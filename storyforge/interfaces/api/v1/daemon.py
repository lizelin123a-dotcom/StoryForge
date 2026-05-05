import asyncio
import json
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from storyforge.application.daemon.services.daemon_orchestrator import DaemonOrchestrator
from storyforge.infrastructure.persistence.daemon_state_repository import load_daemon_state, save_daemon_state
from storyforge.application.daemon.services.sse_event_service import SSEEventManager
from storyforge.infrastructure.ai.openai_adapter import call_llm
from storyforge.infrastructure.persistence.daemon_state_repository import load_latest_daemon_state

router = APIRouter(tags=["daemon"])
orchestrator: DaemonOrchestrator | None = None
sse_manager = SSEEventManager()


class DaemonStartRequest(BaseModel):
    novel_id: str | None = None
    title: str
    world_setting: str
    characters: str
    genre: str
    target_word_count: int
    dissect_source_id: str | None = None
    quality_threshold: int = Field(default=50, ge=0, le=100)
    api_key: str = ""
    api_base_url: str = "https://api.deepseek.com/v1"
    model: str = "deepseek-chat"
    semi_auto: bool = False


class TestLLMRequest(BaseModel):
    api_key: str = ""
    api_base_url: str = "https://api.deepseek.com/v1"
    model: str = "deepseek-chat"


class ReviewDecisionRequest(BaseModel):
    content: str | None = None
    instructions: str = ""


@router.get("/api/v1/daemon/events")
def daemon_events() -> StreamingResponse:
    queue = sse_manager.connect()

    async def event_stream():
        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except asyncio.CancelledError:
            sse_manager.disconnect(queue)
            raise
        finally:
            sse_manager.disconnect(queue)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/api/v1/daemon/start")
def start_daemon(request: DaemonStartRequest) -> dict[str, str]:
    global orchestrator
    if orchestrator is not None and orchestrator.get_state().get("status") == "running":
        raise HTTPException(status_code=409, detail="daemon is already running")
    saved_state = load_daemon_state(request.novel_id) if request.novel_id else None
    orchestrator = DaemonOrchestrator(
        title=request.title,
        world_setting=request.world_setting,
        characters=request.characters,
        genre=request.genre,
        target_word_count=request.target_word_count,
        quality_threshold=request.quality_threshold,
        api_key=request.api_key,
        api_base_url=request.api_base_url,
        model=request.model,
        novel_id=request.novel_id,
        semi_auto=request.semi_auto,
        initial_state=saved_state,
    )
    orchestrator.add_listener(sse_manager.broadcast)
    orchestrator.start()
    return {"status": "started", "novel_id": orchestrator.get_state()["novel_id"]}


@router.post("/api/v1/daemon/pause")
def pause_daemon(novel_id: str | None = None) -> dict[str, str]:
    current = _get_orchestrator(novel_id, allow_saved_pause=True)
    if isinstance(current, DaemonOrchestrator):
        current.pause()
    return {"status": "paused"}


@router.post("/api/v1/daemon/resume")
def resume_daemon(novel_id: str | None = None) -> dict[str, str]:
    current = _get_orchestrator(novel_id)
    current.resume()
    return {"status": "resumed"}


@router.post("/api/v1/daemon/review/approve")
def approve_review(request: ReviewDecisionRequest) -> dict[str, Any]:
    current = _get_orchestrator()
    try:
        node = current.approve_pending_node(request.content, request.instructions)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"status": "approved", "node": node}


@router.post("/api/v1/daemon/review/rewrite")
def rewrite_review(request: ReviewDecisionRequest) -> dict[str, Any]:
    current = _get_orchestrator()
    try:
        node = current.rewrite_pending_node(request.content, request.instructions)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"status": "rewritten", "node": node}


@router.post("/api/v1/daemon/review/rollback")
def rollback_review(request: ReviewDecisionRequest) -> dict[str, Any]:
    current = _get_orchestrator()
    try:
        node = current.rollback_pending_node(request.instructions)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"status": "rolled_back", "node": node}


@router.post("/api/v1/daemon/test-llm")
def test_llm(request: TestLLMRequest) -> dict[str, str]:
    try:
        content = call_llm(
            prompt="回复OK",
            system_prompt="你是一个连接测试助手，只需要简短回复。",
            api_key=request.api_key or None,
            base_url=request.api_base_url or None,
            model=request.model or None,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM connection failed: {exc}") from exc
    return {"status": "ok", "message": content}


@router.get("/api/v1/daemon/status")
def daemon_status(novel_id: str | None = None) -> dict[str, Any]:
    if novel_id:
        current_state = orchestrator.get_state() if orchestrator is not None else None
        if current_state and current_state.get("novel_id") == novel_id:
            return current_state
        saved_state = load_daemon_state(novel_id)
        if saved_state is not None:
            return saved_state
        return _idle_state(novel_id)
    if orchestrator is None:
        latest_state = load_latest_daemon_state()
        if latest_state is not None:
            return latest_state
        return _idle_state()
    return orchestrator.get_state()


def _idle_state(novel_id: str = "") -> dict[str, Any]:
    return {
        "novel_id": novel_id,
        "status": "idle",
        "current_phase": "idle",
        "progress": {"total_chapters": 0, "written_chapters": 0, "total_words": 0, "target_words": 0},
        "foreshadowing_ledger": {"new_hooks": [], "closed_hooks": [], "still_open": []},
        "chapter_summaries": [],
        "chapter_texts": [],
        "baseline_texts": [],
        "conflicts": [],
        "errors": [],
        "retry_count": 0,
        "max_retries": 3,
        "quality_threshold": 50,
        "llm_config": {"api_key": "", "api_base_url": "https://api.deepseek.com/v1", "model": "deepseek-chat"},
        "manual_review": {"enabled": False, "pending": None, "history": [], "instructions": "", "decision": None},
        "runtime_memory": {"chapter_summaries": [], "hooks": [], "facts": []},
        "runtime_state_deltas": [],
        "hook_health_records": [],
    }


def _get_orchestrator(novel_id: str | None = None, allow_saved_pause: bool = False) -> DaemonOrchestrator | dict[str, Any]:
    if orchestrator is not None:
        current_state = orchestrator.get_state()
        if not novel_id or current_state.get("novel_id") == novel_id:
            return orchestrator
    if allow_saved_pause:
        saved_state = load_daemon_state(novel_id) if novel_id else load_latest_daemon_state()
        if saved_state is not None:
            saved_state["status"] = "paused"
            saved_state["current_phase"] = saved_state.get("current_phase") or "idle"
            save_daemon_state(saved_state)
            sse_manager.broadcast({"type": "paused", "data": {"reason": "saved_state_pause"}, "state": saved_state})
            return saved_state
    raise HTTPException(status_code=404, detail="daemon is not started")
