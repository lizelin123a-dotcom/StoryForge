import asyncio
import json
from threading import Lock
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from storyforge.application.daemon.services.daemon_orchestrator import DaemonOrchestrator
from storyforge.application.daemon.services.sse_event_service import SSEEventManager
from storyforge.infrastructure.ai.openai_adapter import call_llm
from storyforge.infrastructure.persistence.daemon_state_repository import load_daemon_state, load_latest_daemon_state, save_daemon_state
from storyforge.infrastructure.persistence.novel_repository import save_chapter_text, save_node_draft

router = APIRouter(tags=["daemon"])
orchestrators: dict[str, DaemonOrchestrator] = {}
orchestrators_lock = Lock()
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
    novel_id: str | None = None
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
    saved_state = load_daemon_state(request.novel_id) if request.novel_id else None
    if saved_state is not None:
        saved_state = _normalize_resume_state(saved_state)
    candidate = DaemonOrchestrator(
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
    novel_id = str(candidate.get_state()["novel_id"])
    with orchestrators_lock:
        existing = orchestrators.get(novel_id)
        if existing is not None and existing.get_state().get("status") == "running":
            raise HTTPException(status_code=409, detail="daemon is already running for this novel")
        orchestrators[novel_id] = candidate
    candidate.add_listener(sse_manager.broadcast)
    candidate.start()
    return {"status": "started", "novel_id": novel_id}


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
    current = _get_running_orchestrator(request.novel_id) if request.novel_id else _latest_running_orchestrator()
    if current is None:
        node = _resolve_saved_pending_review(request, "approved")
        return {"status": "approved", "node": node, "source": "saved_state"}
    try:
        node = current.approve_pending_node(request.content, request.instructions)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"status": "approved", "node": node}


@router.post("/api/v1/daemon/review/rewrite")
def rewrite_review(request: ReviewDecisionRequest) -> dict[str, Any]:
    current = _get_running_orchestrator(request.novel_id) if request.novel_id else _latest_running_orchestrator()
    if current is None:
        node = _resolve_saved_pending_review(request, "rewritten")
        return {"status": "rewritten", "node": node, "source": "saved_state"}
    try:
        node = current.rewrite_pending_node(request.content, request.instructions)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"status": "rewritten", "node": node}


@router.post("/api/v1/daemon/review/rollback")
def rollback_review(request: ReviewDecisionRequest) -> dict[str, Any]:
    current = _get_running_orchestrator(request.novel_id) if request.novel_id else _latest_running_orchestrator()
    if current is None:
        node = _resolve_saved_pending_review(request, "rolled_back")
        return {"status": "rolled_back", "node": node, "source": "saved_state"}
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
        current = _get_running_orchestrator(novel_id)
        if current is not None:
            return current.get_state()
        saved_state = load_daemon_state(novel_id)
        if saved_state is not None:
            return saved_state
        return _idle_state(novel_id)
    latest = _latest_running_orchestrator()
    if latest is not None:
        return latest.get_state()
    latest_state = load_latest_daemon_state()
    if latest_state is not None:
        return latest_state
    return _idle_state()


def _resolve_saved_pending_review(request: ReviewDecisionRequest, decision: str) -> dict[str, Any]:
    state = load_daemon_state(request.novel_id) if request.novel_id else load_latest_daemon_state()
    if state is None:
        raise HTTPException(status_code=404, detail="daemon is not started")
    manual = dict(state.get("manual_review") or {})
    pending = manual.get("pending")
    if not pending:
        raise HTTPException(status_code=409, detail="no pending review node")
    resolved = dict(pending)
    if request.content is not None and decision != "rolled_back":
        resolved["content"] = request.content
    resolved["decision"] = decision
    resolved["instructions"] = request.instructions
    manual.setdefault("history", []).append(resolved)
    manual["pending"] = None
    manual["decision"] = {"type": decision, "content": request.content, "instructions": request.instructions}
    manual["instructions"] = request.instructions
    state["manual_review"] = manual
    novel_id = str(state.get("novel_id") or request.novel_id or "")
    chapter_index = int(resolved.get("chapter_index") or 1)
    node_index = int(resolved.get("node_index") or 1)
    node_type = str(resolved.get("node_type") or "节点")
    content = str(resolved.get("content") or "")
    if decision != "rolled_back" and novel_id and content:
        save_node_draft(novel_id, chapter_index, node_index, node_type, content, locked=True, source="manual_review", sync_chapter=False, status="approved", appended_to_chapter=True)
        chapter_texts = list(state.get("chapter_texts") or [])
        while len(chapter_texts) < chapter_index:
            chapter_texts.append("")
        existing = str(chapter_texts[chapter_index - 1] or "")
        chapter_texts[chapter_index - 1] = f"{existing}{chr(10) + chr(10) if existing else ''}{content}"
        state["chapter_texts"] = chapter_texts
        state["baseline_texts"] = chapter_texts
        progress = dict(state.get("progress") or {})
        progress["written_chapters"] = min(int(progress.get("written_chapters") or 0), len(chapter_texts))
        progress["total_words"] = sum(len(str(text or "")) for text in chapter_texts)
        state["progress"] = progress
        card = dict(state.get("writing_card") or {})
        completed = sorted(set([*(card.get("completed_nodes") or []), node_index]))
        card.update({"chapter_index": chapter_index, "node_index": node_index + 1, "completed_nodes": completed, "status": "node_approved", "next_step": f"第 {node_index} 节已写入正文"})
        state["writing_card"] = card
        save_chapter_text(novel_id, chapter_index, chapter_texts[chapter_index - 1])
    state["status"] = "paused"
    state["current_phase"] = "reviewing"
    save_daemon_state(state)
    sse_manager.broadcast({"type": "node_review_resolved", "data": {"decision": decision, "node": resolved, "source": "saved_state"}, "state": state})
    return resolved


def _normalize_resume_state(state: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(state)
    chapter_texts = list(normalized.get("chapter_texts") or [])
    progress = dict(normalized.get("progress") or {})
    progress["written_chapters"] = min(int(progress.get("written_chapters") or 0), len(chapter_texts))
    progress["total_words"] = sum(len(str(text or "")) for text in chapter_texts)
    normalized["progress"] = progress
    normalized["chapter_texts"] = chapter_texts
    normalized["baseline_texts"] = list(chapter_texts)
    card = dict(normalized.get("writing_card") or {})
    card.setdefault("chapter_index", max(1, int(progress.get("written_chapters") or 0) + 1))
    card.setdefault("node_index", 1)
    card.setdefault("planned_nodes", card.get("nodes_total", 0))
    card.setdefault("completed_nodes", [])
    card.setdefault("status", "idle")
    card.setdefault("chapter_title", f"第 {card.get('chapter_index', 1)} 章")
    card.setdefault("next_step", "等待开始写作")
    normalized["writing_card"] = card
    manual = dict(normalized.get("manual_review") or {})
    if not manual.get("pending"):
        manual["decision"] = None
    normalized["manual_review"] = manual
    return normalized


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
        "writing_card": {"chapter_index": 1, "node_index": 1, "planned_nodes": 0, "completed_nodes": [], "status": "idle", "chapter_title": "第 1 章", "next_step": "等待开始写作"},
        "runtime_memory": {"chapter_summaries": [], "hooks": [], "facts": []},
        "runtime_state_deltas": [],
        "hook_health_records": [],
    }


def _get_orchestrator(novel_id: str | None = None, allow_saved_pause: bool = False) -> DaemonOrchestrator | dict[str, Any]:
    current = _get_running_orchestrator(novel_id) if novel_id else _latest_running_orchestrator()
    if current is not None:
        return current
    if allow_saved_pause:
        saved_state = load_daemon_state(novel_id) if novel_id else load_latest_daemon_state()
        if saved_state is not None:
            saved_state["status"] = "paused"
            saved_state["current_phase"] = saved_state.get("current_phase") or "idle"
            save_daemon_state(saved_state)
            sse_manager.broadcast({"type": "paused", "data": {"reason": "saved_state_pause"}, "state": saved_state})
            return saved_state
    raise HTTPException(status_code=404, detail="daemon is not started")


def _get_running_orchestrator(novel_id: str) -> DaemonOrchestrator | None:
    with orchestrators_lock:
        return orchestrators.get(novel_id)


def _latest_running_orchestrator() -> DaemonOrchestrator | None:
    with orchestrators_lock:
        if not orchestrators:
            return None
        return next(reversed(orchestrators.values()))
