import asyncio
import json
from threading import Lock
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from storyforge.application.daemon.services.daemon_orchestrator import DaemonOrchestrator, _build_rollback_instruction
from storyforge.application.planner.services.chapter_outliner import generate_chapter_outline
from storyforge.application.daemon.services.sse_event_service import SSEEventManager
from storyforge.infrastructure.ai.openai_adapter import call_llm
from storyforge.infrastructure.persistence.daemon_state_repository import load_daemon_state, load_latest_daemon_state, save_daemon_state
from storyforge.infrastructure.persistence.database import SessionLocal, init_db
from storyforge.infrastructure.persistence.models.novel import ChapterModel, NodeDraftModel
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
    planning_model: str = ""
    writing_model: str = ""
    writing_api_key: str = ""
    writing_api_base_url: str = ""
    review_model: str = ""
    fast_model: str = ""
    semi_auto: bool = False


class TestLLMRequest(BaseModel):
    api_key: str = ""
    api_base_url: str = "https://api.deepseek.com/v1"
    model: str = "deepseek-chat"


class ReviewDecisionRequest(BaseModel):
    novel_id: str | None = None
    content: str | None = None
    instructions: str = ""
    revision_id: str = ""


class RewriteChapterRequest(BaseModel):
    novel_id: str
    chapter_index: int = Field(ge=1)
    reset_outline: bool = False


class RegenerateOutlineRequest(BaseModel):
    novel_id: str
    chapter_index: int = Field(ge=1)


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
        model=request.writing_model or request.model,
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
    _apply_model_roles(candidate, request)
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
        node = current.approve_pending_node(request.content, request.instructions, request.revision_id)
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
        node = current.rewrite_pending_node(request.content, request.instructions, request.revision_id)
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
        node = current.rollback_pending_node(request.instructions, request.revision_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"status": "rolled_back", "node": node}


@router.post("/api/v1/daemon/regenerate-outline")
def regenerate_outline(request: RegenerateOutlineRequest) -> dict[str, Any]:
    state = _regenerate_chapter_outline_only(request.novel_id, request.chapter_index)
    sse_manager.broadcast({"type": "outline_ready", "data": state.get("current_chapter_outline") or {}, "state": state})
    return {"status": "outline_regenerated", "chapter_index": request.chapter_index, "state": state}


@router.post("/api/v1/daemon/rewrite-chapter")
def rewrite_chapter(request: RewriteChapterRequest) -> dict[str, Any]:
    state = _reset_chapter_for_rewrite(request.novel_id, request.chapter_index, request.reset_outline)
    sse_manager.broadcast({"type": "chapter_rewrite_reset", "data": {"chapter_index": request.chapter_index, "reset_outline": request.reset_outline}, "state": state})
    return {"status": "ready_to_rewrite", "chapter_index": request.chapter_index, "reset_outline": request.reset_outline, "state": state, "writer_note": "本章正文和已通过小节已清空，可以从第 1 节重新写。"}


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
            saved_state = _normalize_stale_state(saved_state)
            save_daemon_state(saved_state)
            return saved_state
        return _idle_state(novel_id)
    latest = _latest_running_orchestrator()
    if latest is not None:
        return latest.get_state()
    latest_state = load_latest_daemon_state()
    if latest_state is not None:
        latest_state = _normalize_stale_state(latest_state)
        save_daemon_state(latest_state)
        return latest_state
    return _idle_state()


def _regenerate_chapter_outline_only(novel_id: str, chapter_index: int) -> dict[str, Any]:
    current = _get_running_orchestrator(novel_id)
    state = current.state if current is not None else (load_daemon_state(novel_id) or _idle_state(novel_id))
    config = dict(state.get("llm_config") or {})

    def llm(prompt: str, system_prompt: str = "", json_mode: bool = False) -> str:
        return call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            json_mode=json_mode,
            api_key=config.get("api_key") or None,
            base_url=config.get("api_base_url") or None,
            model=config.get("planning_model") or config.get("model") or None,
        )

    act_plans = state.get("act_plans") if isinstance(state.get("act_plans"), list) else []
    chapter_plan: dict[str, Any] = {"chapter_index": chapter_index, "core_event": "按当前案头设定重做本章章纲", "target_word_count": 3000, "emotion_tone": "期待"}
    act_plan: dict[str, Any] = {"chapters": [chapter_plan]}
    for act in act_plans:
        if not isinstance(act, dict):
            continue
        for chapter in act.get("chapters", []) or []:
            if int(chapter.get("chapter_index") or 0) == chapter_index:
                chapter_plan = dict(chapter)
                act_plan = dict(act)
                break
    assets = state.get("novel_assets") or {}
    override = str(assets.get(f"chapter_outline:{chapter_index}") or "").strip()
    chapter_function = str(chapter_plan.get("core_event") or chapter_plan.get("title") or "推进本章主线")
    outline_function = f"{chapter_function}\n\n作者指定章纲覆盖：{override}" if override else chapter_function
    outline = generate_chapter_outline(act_plan, chapter_index, outline_function, llm=llm)
    if override:
        outline["author_override"] = override
        outline.setdefault("memo", {})["current_task"] = override
    state["current_chapter_outline"] = {"chapter_index": chapter_index, "chapter_function": chapter_function, "outline": outline, "nodes": outline.get("nodes") or [], "refreshed": True}
    state["novel_assets"] = {**assets, "assets_dirty": "false", f"chapter_outline_dirty:{chapter_index}": "false"}
    card = dict(state.get("writing_card") or {})
    card.update({"chapter_index": chapter_index, "status": "outline_refreshed", "next_step": "章纲已刷新，可选择重写当前小节或重写本章"})
    state["writing_card"] = card
    save_daemon_state(state)
    return state


def _reset_chapter_for_rewrite(novel_id: str, chapter_index: int, reset_outline: bool = False) -> dict[str, Any]:
    init_db()
    current = _get_running_orchestrator(novel_id)
    state = current.state if current is not None else (load_daemon_state(novel_id) or _idle_state(novel_id))
    chapter_texts = list(state.get("chapter_texts") or [])
    while len(chapter_texts) < chapter_index:
        chapter_texts.append("")
    chapter_texts[chapter_index - 1] = ""
    state["chapter_texts"] = chapter_texts
    state["baseline_texts"] = list(chapter_texts)
    state["current_phase"] = "rewrite_ready"
    state["status"] = "idle"
    progress = dict(state.get("progress") or {})
    progress["written_chapters"] = min(int(progress.get("written_chapters") or 0), max(0, chapter_index - 1))
    progress["total_words"] = sum(len(str(text or "")) for text in chapter_texts)
    state["progress"] = progress
    manual = dict(state.get("manual_review") or {})
    manual["pending"] = None
    manual["decision"] = None
    manual["instructions"] = ""
    state["manual_review"] = manual
    state["locked_nodes"] = [node for node in (state.get("locked_nodes") or []) if int(node.get("chapter_index") or 0) != chapter_index]
    card = dict(state.get("writing_card") or {})
    card.update({"chapter_index": chapter_index, "node_index": 1, "completed_nodes": [], "status": "chapter_rewrite_ready", "next_step": "本章已清空，正在准备重新写第 1 节", "chapter_title": f"第 {chapter_index} 章"})
    state["writing_card"] = card

    with SessionLocal() as session:
        session.query(NodeDraftModel).filter(NodeDraftModel.novel_id == novel_id, NodeDraftModel.chapter_index == chapter_index).delete()
        chapter_id = f"{novel_id}:chapter:{chapter_index}"
        chapter = session.get(ChapterModel, chapter_id)
        if chapter is not None:
            chapter.content = ""
            chapter.word_count = 0
        session.commit()
    save_chapter_text(novel_id, chapter_index, "")
    save_daemon_state(state)
    with orchestrators_lock:
        existing = orchestrators.get(novel_id)
        if existing is not None:
            existing.state["status"] = "completed"
            existing.state["current_phase"] = "rewrite_reset"
            orchestrators.pop(novel_id, None)
    return state


def _apply_model_roles(candidate: DaemonOrchestrator, request: DaemonStartRequest) -> None:
    state = candidate.state
    config = dict(state.get("llm_config") or {})
    config.update({
        "model": request.model,
        "planning_model": request.planning_model or request.model,
        "writing_model": request.writing_model or request.model,
        "writing_api_key": request.writing_api_key or request.api_key,
        "writing_api_base_url": request.writing_api_base_url or request.api_base_url,
        "review_model": request.review_model or request.model,
        "fast_model": request.fast_model or request.writing_model or request.model,
    })
    state["llm_config"] = config
    state.setdefault("writing_card", {})["model_roles"] = {
        "planning": config["planning_model"],
        "writing": config["writing_model"],
        "review": config["review_model"],
        "fast": config["fast_model"],
    }


def _resolve_saved_pending_review(request: ReviewDecisionRequest, decision: str) -> dict[str, Any]:
    state = load_daemon_state(request.novel_id) if request.novel_id else load_latest_daemon_state()
    if state is None:
        raise HTTPException(status_code=404, detail="daemon is not started")
    manual = dict(state.get("manual_review") or {})
    pending = manual.get("pending")
    if not pending:
        raise HTTPException(status_code=409, detail="no pending review node")
    if request.revision_id and str(pending.get("revision_id") or "") != request.revision_id:
        raise HTTPException(status_code=409, detail="stale review revision")
    resolved = dict(pending)
    if request.content is not None and decision != "rolled_back":
        resolved["content"] = request.content
    resolved["decision"] = decision
    resolved["instructions"] = request.instructions
    manual.setdefault("history", []).append(resolved)
    novel_id = str(state.get("novel_id") or request.novel_id or "")
    chapter_index = int(resolved.get("chapter_index") or 1)
    node_index = int(resolved.get("node_index") or 1)
    node_type = str(resolved.get("node_type") or "节点")
    content = str(resolved.get("content") or "")
    if decision == "rolled_back":
        rewrite_instruction = _build_rollback_instruction(request.instructions)
        rejected = str(pending.get("content") or "")
        manual["pending"] = pending
        manual["last_rejected"] = {"chapter_index": chapter_index, "node_index": node_index, "content": rejected[:1200], "reason": rewrite_instruction}
        manual["decision"] = {"type": decision, "content": None, "instructions": rewrite_instruction}
        manual["instructions"] = f"{rewrite_instruction}\n\n上一版已被拒绝，禁止复用其写法和重点。上一版节选：{rejected[:800]}"
    else:
        manual["pending"] = None
        manual["decision"] = {"type": decision, "content": request.content, "instructions": request.instructions}
        manual["instructions"] = request.instructions
    state["manual_review"] = manual
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
    if decision == "rolled_back":
        card = dict(state.get("writing_card") or {})
        card.update({"chapter_index": chapter_index, "node_index": node_index, "status": "node_writing", "next_step": f"正在给第 {node_index} 节换一版"})
        state["writing_card"] = card
    state["status"] = "paused"
    state["current_phase"] = "reviewing"
    save_daemon_state(state)
    sse_manager.broadcast({"type": "node_review_resolved", "data": {"decision": decision, "node": resolved, "source": "saved_state"}, "state": state})
    return resolved


def _normalize_stale_state(state: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(state)
    if normalized.get("status") == "running":
        normalized["status"] = "idle"
        normalized["current_phase"] = "stopped"
        card = dict(normalized.get("writing_card") or {})
        if card.get("status") not in {"node_review", "chapter_rewrite_ready"}:
            card["status"] = "stopped"
        card["next_step"] = "上次写作进程已随终端关闭而终止，需手动重新启动。"
        normalized["writing_card"] = card
    manual = dict(normalized.get("manual_review") or {})
    if normalized.get("status") != "running":
        manual["decision"] = None
    normalized["manual_review"] = manual
    return normalized


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
        "llm_config": {"api_key": "", "api_base_url": "https://api.deepseek.com/v1", "model": "deepseek-chat", "planning_model": "", "writing_model": "deepseek-chat", "review_model": "", "fast_model": ""},
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
