import time
from copy import deepcopy
from threading import Lock, Thread
from typing import Any, Callable, Literal
from uuid import uuid4

from storyforge.application.analyst.services.conflict_tracker import track_conflicts
from storyforge.application.analyst.services.voice_drift_service import detect_voice_drift
from storyforge.application.audit.services.chapter_review_service import review_chapter
from storyforge.application.audit.services.outline_check_service import check_chapter_outline
from storyforge.application.planner.services.act_planner import generate_act_plans
from storyforge.application.planner.services.chapter_outliner import generate_chapter_outline
from storyforge.application.planner.services.fallback import fallback_notice
from storyforge.application.planner.services.macro_planner import generate_macro_outline
from storyforge.application.writer.services.consistency_checker import check_node_consistency
from storyforge.application.writer.services.four_questions import answer_four_questions
from storyforge.application.writer.services.node_generator import generate_node_content
from storyforge.application.daemon.services.context_governance import apply_review_delta, build_governed_context
from storyforge.domain.dissect.dissected_chapter import DissectedChapter
from storyforge.domain.node.node import ChapterNode
from storyforge.infrastructure.ai.openai_adapter import call_llm
from storyforge.infrastructure.persistence.daemon_state_repository import save_daemon_state
from storyforge.infrastructure.persistence.novel_repository import get_novel_assets, list_node_drafts, save_chapter_text, save_node_draft

Listener = Callable[[dict[str, Any]], None]


class DaemonOrchestrator:
    def __init__(
        self,
        title: str,
        world_setting: str,
        characters: str,
        genre: str,
        target_word_count: int,
        dissected_chapters: list[DissectedChapter] | None = None,
        quality_threshold: int = 50,
        max_retries: int = 3,
        api_key: str = "",
        api_base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-chat",
        novel_id: str | None = None,
        semi_auto: bool = False,
        initial_state: dict[str, Any] | None = None,
    ) -> None:
        self.title = title
        self.world_setting = world_setting
        self.characters = characters
        self.genre = genre
        self.target_word_count = target_word_count
        self.dissected_chapters = dissected_chapters or []
        self.listeners: list[Listener] = []
        self.thread: Thread | None = None
        self.state_lock = Lock()
        self.state = self._build_initial_state(
            novel_id=novel_id or str(uuid4()),
            target_word_count=target_word_count,
            quality_threshold=quality_threshold,
            max_retries=max_retries,
            api_key=api_key,
            api_base_url=api_base_url,
            model=model,
            semi_auto=semi_auto,
            initial_state=initial_state,
        )

    def _build_initial_state(
        self,
        novel_id: str,
        target_word_count: int,
        quality_threshold: int,
        max_retries: int,
        api_key: str,
        api_base_url: str,
        model: str,
        semi_auto: bool,
        initial_state: dict[str, Any] | None,
    ) -> dict[str, Any]:
        state = deepcopy(initial_state) if initial_state else {}
        chapter_texts = list(state.get("chapter_texts") or [])
        progress = dict(state.get("progress") or {})
        persisted_written = sum(1 for text in chapter_texts if str(text or "").strip())
        progress["written_chapters"] = max(int(progress.get("written_chapters") or 0), persisted_written)
        progress["total_chapters"] = int(progress.get("total_chapters") or 0)
        progress["total_words"] = sum(len(str(text or "")) for text in chapter_texts)
        progress["target_words"] = target_word_count
        manual = dict(state.get("manual_review") or {})
        manual["enabled"] = semi_auto
        if semi_auto:
            manual.setdefault("pending", None)
            manual.setdefault("instructions", "")
        else:
            manual["pending"] = None
            manual["instructions"] = ""
        manual.setdefault("history", [])
        manual.setdefault("decision", None)
        state.update(
            {
                "novel_id": novel_id,
                "status": "idle",
                "current_phase": state.get("current_phase", "idle"),
                "progress": progress,
                "foreshadowing_ledger": state.get("foreshadowing_ledger") or {"new_hooks": [], "closed_hooks": [], "still_open": []},
                "chapter_summaries": state.get("chapter_summaries") or [],
                "chapter_texts": chapter_texts,
                "baseline_texts": state.get("baseline_texts") or chapter_texts,
                "conflicts": state.get("conflicts") or [],
                "errors": state.get("errors") or [],
                "retry_count": 0,
                "max_retries": max_retries,
                "quality_threshold": quality_threshold,
                "llm_config": {"api_key": api_key, "api_base_url": api_base_url, "model": model},
                "manual_review": manual,
                "runtime_memory": state.get("runtime_memory") or {"chapter_summaries": [], "hooks": [], "facts": []},
                "runtime_state_deltas": state.get("runtime_state_deltas") or [],
                "hook_health_records": state.get("hook_health_records") or [],
                "novel_assets": state.get("novel_assets") or get_novel_assets(novel_id),
                "locked_nodes": state.get("locked_nodes") or list_node_drafts(novel_id, locked_only=True),
            }
        )
        return state

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        self.state["status"] = "running"
        self._persist_state()
        self.thread = Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def pause(self) -> None:
        self.state["status"] = "paused"
        self._notify("paused", {"reason": "manual_pause"})

    def resume(self) -> None:
        if self.state["status"] == "paused":
            self.state["status"] = "running"
            self._notify("resumed", {"status": "running"})

    def get_state(self) -> dict[str, Any]:
        with self.state_lock:
            return deepcopy(self.state)

    def get_progress(self) -> dict[str, Any]:
        with self.state_lock:
            return deepcopy(self.state["progress"])

    def add_listener(self, listener: Listener) -> None:
        self.listeners.append(listener)

    def approve_pending_node(self, content: str | None = None, instructions: str = "") -> dict[str, Any]:
        return self._resolve_pending_node("approved", content, instructions)

    def rewrite_pending_node(self, content: str | None = None, instructions: str = "") -> dict[str, Any]:
        return self._resolve_pending_node("rewritten", content, instructions)

    def rollback_pending_node(self, instructions: str = "") -> dict[str, Any]:
        return self._resolve_pending_node("rolled_back", None, instructions)

    def _resolve_pending_node(self, decision: Literal["approved", "rewritten", "rolled_back"], content: str | None, instructions: str) -> dict[str, Any]:
        manual = self.state.setdefault("manual_review", {"enabled": False, "pending": None, "history": [], "instructions": "", "decision": None})
        pending = manual.get("pending")
        if not pending:
            raise ValueError("no pending review node")
        resolved = dict(pending)
        if content is not None:
            resolved["content"] = content
        resolved["decision"] = decision
        resolved["instructions"] = instructions
        manual.setdefault("history", []).append(resolved)
        manual["pending"] = None
        manual["decision"] = {"type": decision, "content": content, "instructions": instructions}
        manual["instructions"] = instructions
        self._notify("node_review_resolved", {"decision": decision, "node": resolved})
        return resolved

    def _run_loop(self) -> None:
        try:
            llm = self._get_llm()
            self.state["current_phase"] = "planning"
            macro_outline = generate_macro_outline(
                title=self.title,
                world_setting=self.world_setting,
                characters=self.characters,
                target_word_count=self.target_word_count,
                genre=self.genre,
                dissected_chapters=self.dissected_chapters,
                llm=llm,
            )
            self.state["macro_outline"] = macro_outline
            self._notify_fallback_if_needed(macro_outline)
            self._notify("planning_complete", {"acts": macro_outline.get("acts", [])})

            self.state["current_phase"] = "acts"
            act_plans = generate_act_plans(macro_outline, llm=llm)
            self.state["act_plans"] = act_plans
            for act_plan in act_plans:
                self._notify_fallback_if_needed(act_plan)
            total_chapters = sum(len(act.get("chapters", [])) for act in act_plans)
            if total_chapters <= 0:
                total_chapters = sum(int(act.get("chapter_count", 0)) for act in macro_outline.get("acts", [])) or 1
            self.state["progress"]["total_chapters"] = total_chapters
            self._notify("act_plans_complete", {"act_plans": act_plans})

            for act in act_plans:
                chapters = act.get("chapters", []) or [{"chapter_index": 1, "core_event": "开篇入局", "target_word_count": 3000, "emotion_tone": "期待"}]
                for chapter in chapters:
                    self._wait_if_paused()
                    if self.state["status"] in {"error", "completed"}:
                        return
                    planned_index = int(chapter.get("chapter_index", self.state["progress"]["written_chapters"] + 1))
                    chapter_index = self._next_writable_chapter_index(planned_index)
                    if chapter_index != planned_index:
                        chapter = {**chapter, "chapter_index": chapter_index}
                    self._write_chapter_with_retries(act, chapter)
                    if self.state["progress"]["total_words"] >= self.target_word_count:
                        self.state["status"] = "completed"
                        self._notify("novel_complete", {
                            "novel_id": self.state["novel_id"],
                            "total_chapters": self.state["progress"]["written_chapters"],
                            "total_words": self.state["progress"]["total_words"],
                        })
                        return

            self.state["status"] = "completed"
            self._notify("novel_complete", {
                "novel_id": self.state["novel_id"],
                "total_chapters": self.state["progress"]["written_chapters"],
                "total_words": self.state["progress"]["total_words"],
            })
        except Exception as exc:
            self.state["status"] = "error"
            self.state["errors"].append(str(exc))
            self._notify("error", {"message": str(exc), "fatal": True})

    def _write_chapter_with_retries(self, act: dict[str, Any], chapter: dict[str, Any]) -> None:
        self.state["retry_count"] = 0
        while self.state["retry_count"] <= self.state["max_retries"]:
            result = self._write_single_chapter(act, chapter)
            if result["quality_score"] >= self.state["quality_threshold"]:
                self.state["retry_count"] = 0
                return
            self.state["retry_count"] += 1
            if self.state["retry_count"] >= self.state["max_retries"]:
                self.state["status"] = "paused"
                self._notify("paused", {"reason": "quality_circuit_breaker", "chapter_index": result["chapter_index"], "quality_score": result["quality_score"]})
                return
            self._rewrite_with_feedback(result["chapter_index"], result["review_data"])

    def _write_single_chapter(self, act: dict[str, Any], chapter: dict[str, Any]) -> dict[str, Any]:
        self._wait_if_paused()
        chapter_index = self._next_writable_chapter_index(int(chapter.get("chapter_index", self.state["progress"]["written_chapters"] + 1)))
        chapter_function = str(chapter.get("core_event", "推进主线"))
        self.state["current_phase"] = "writing"
        llm = self._get_llm()
        nodes = generate_chapter_outline(act, chapter_index, chapter_function, llm=llm)
        self._notify("outline_ready", {"chapter_index": chapter_index, "nodes": [node.model_dump() for node in nodes]})

        generated_nodes: list[ChapterNode] = []
        for node in nodes:
            self._wait_if_paused()
            context = build_governed_context(
                chapter_index=chapter_index,
                story_bible={"world_setting": self.world_setting, "characters": self.characters, "genre": self.genre},
                chapter_summaries=self.state["chapter_summaries"],
                baseline_texts=self.state["baseline_texts"],
                foreshadowing_ledger=self.state["foreshadowing_ledger"],
                manual_instructions=self.state.get("manual_review", {}).get("instructions", ""),
                novel_assets=self.state.get("novel_assets") or get_novel_assets(self.state["novel_id"]),
                locked_nodes=self.state.get("locked_nodes") or list_node_drafts(self.state["novel_id"], locked_only=True),
            )
            questions = answer_four_questions(node, context, llm=llm)
            if getattr(questions, "_fallback_reason", ""):
                self._notify("llm_fallback_used", {"stage": "four_questions", "reason": str(getattr(questions, "_fallback_reason"))})
            filled = generate_node_content(node, context, questions, llm=llm)
            if filled.content and "【本地写作教学规则生成】" in filled.content:
                self._notify("llm_fallback_used", {"stage": "node_content", "reason": "node generation failed; local writing rules used"})
            locked_override = self._get_locked_node(chapter_index, filled.index)
            if locked_override:
                filled = filled.model_copy(update={"content": str(locked_override.get("content") or filled.content or "")})
                self._notify("locked_node_applied", {"chapter_index": chapter_index, "node_index": filled.index, "node_type": filled.node_type})
            else:
                save_node_draft(self.state["novel_id"], chapter_index, filled.index, filled.node_type, filled.content or "", locked=False, source="ai_draft")
            self._notify(
                "node_draft_generated",
                {
                    "chapter_index": chapter_index,
                    "node_index": filled.index,
                    "node_type": filled.node_type,
                    "content": filled.content,
                    "generation_logic": self._build_generation_logic(node, questions, context),
                },
            )
            filled = self._wait_for_node_review(chapter_index, filled)
            if filled is None:
                continue
            generated_nodes.append(filled)
            self._notify(
                "node_generated",
                {
                    "chapter_index": chapter_index,
                    "node_index": filled.index,
                    "node_type": filled.node_type,
                    "content": filled.content,
                    "reviewed": True,
                },
            )

        consistency = check_node_consistency(generated_nodes)
        outline_check = check_chapter_outline(generated_nodes)
        chapter_text = "\n\n".join(node.content or "" for node in generated_nodes)

        self.state["current_phase"] = "reviewing"
        review_data = review_chapter(
            novel_id=self.state["novel_id"],
            chapter_index=chapter_index,
            chapter_text=chapter_text,
            previous_summaries=self.state["chapter_summaries"],
            foreshadowing_ledger=self.state["foreshadowing_ledger"],
            llm=llm,
        )
        conflict_data = track_conflicts(chapter_text, chapter_index, self.state["conflicts"], llm=llm)
        voice_data = detect_voice_drift(chapter_text, self.state["baseline_texts"][-3:])
        self._notify_fallback_if_needed(review_data)
        review_data["consistency"] = consistency
        review_data["outline_check"] = outline_check
        review_data["conflict_tracking"] = conflict_data
        review_data["voice_drift"] = voice_data
        quality_score = self._calculate_quality_score(review_data)
        review_data["quality_score"] = quality_score

        if quality_score >= self.state["quality_threshold"]:
            self._commit_chapter(chapter_index, chapter_text, review_data, conflict_data)
            apply_review_delta(self.state, chapter_index, review_data, chapter_text)

        self._notify("chapter_reviewed", {"chapter_index": chapter_index, "review_data": review_data})
        self._notify("writing_progress", self.get_progress())
        return {"chapter_index": chapter_index, "review_data": review_data, "quality_score": quality_score}

    def _next_writable_chapter_index(self, planned_index: int) -> int:
        chapter_texts = self.state.get("chapter_texts") or []
        first_empty = next((index + 1 for index, text in enumerate(chapter_texts) if not str(text or "").strip()), len(chapter_texts) + 1)
        return max(planned_index, first_empty)

    def _get_locked_node(self, chapter_index: int, node_index: int) -> dict[str, Any] | None:
        locked_nodes = self.state.get("locked_nodes") or list_node_drafts(self.state["novel_id"], locked_only=True)
        self.state["locked_nodes"] = locked_nodes
        for node in locked_nodes:
            if int(node.get("chapter_index") or 0) == chapter_index and int(node.get("node_index") or 0) == node_index and node.get("locked"):
                return node
        return None

    def _commit_chapter(self, chapter_index: int, chapter_text: str, review_data: dict[str, Any], conflict_data: dict[str, Any]) -> None:
        while len(self.state["chapter_texts"]) < chapter_index:
            self.state["chapter_texts"].append("")
        existing = str(self.state["chapter_texts"][chapter_index - 1] or "")
        committed_text = existing or chapter_text
        self.state["chapter_texts"][chapter_index - 1] = committed_text
        self.state["baseline_texts"] = list(self.state["chapter_texts"])
        self.state["chapter_summaries"].append(str(review_data.get("chapter_summary", "")))
        self.state["conflicts"] = conflict_data.get("current_conflicts", self.state["conflicts"])
        foreshadowing = review_data.get("foreshadowing", {})
        self.state["foreshadowing_ledger"] = {
            "new_hooks": foreshadowing.get("new_hooks", []),
            "closed_hooks": foreshadowing.get("closed_hooks", []),
            "still_open": foreshadowing.get("still_open", []),
        }
        self.state["progress"]["written_chapters"] = max(int(self.state["progress"].get("written_chapters") or 0), chapter_index)
        self.state["progress"]["total_words"] = sum(len(str(text or "")) for text in self.state["chapter_texts"])
        save_chapter_text(self.state["novel_id"], chapter_index, committed_text)

    def _calculate_quality_score(self, review_data: dict[str, Any]) -> int:
        score = 50
        shuang = review_data.get("shuang_analysis", {})
        if shuang.get("types_used") or shuang.get("main_type") or shuang.get("frequency"):
            score += 10
        if review_data.get("rhythm", {}).get("pattern") == "匹配":
            score += 10
        elif review_data.get("rhythm", {}).get("pattern") == "部分匹配":
            score += 5
        if not review_data.get("information_gap", {}).get("no_gap_warning", True):
            score += 10
        if not review_data.get("voice_drift", {}).get("drift_detected", False):
            score += 10
        foreshadowing = review_data.get("foreshadowing", {})
        if isinstance(foreshadowing, dict) and len(foreshadowing.get("still_open", [])) <= 5:
            score += 5
        if not review_data.get("consistency", {}).get("passed", True):
            score -= 10
        if not review_data.get("outline_check", {}).get("passed", True):
            score -= 10
        return min(max(score, 0), 100)

    def _wait_for_node_review(self, chapter_index: int, node: ChapterNode) -> ChapterNode | None:
        manual = self.state.setdefault("manual_review", {"enabled": False, "pending": None, "history": [], "instructions": "", "decision": None})
        if not manual.get("enabled"):
            manual["pending"] = None
            manual["decision"] = None
            return node
        manual["decision"] = None
        manual["pending"] = {
            "chapter_index": chapter_index,
            "node_index": node.index,
            "node_type": node.node_type,
            "trigger_point": node.trigger_point,
            "emotion_purpose": node.emotion_purpose,
            "reader_expectation": node.reader_expectation,
            "content": node.content or "",
        }
        self._notify("node_review_required", dict(manual["pending"]))
        while manual.get("pending") and self.state.get("status") == "running" and manual.get("enabled"):
            time.sleep(0.5)
        decision = manual.get("decision") or {}
        manual["decision"] = None
        if decision.get("type") == "rolled_back":
            return None
        if decision.get("content") is not None:
            content = str(decision.get("content") or "")
            save_node_draft(self.state["novel_id"], chapter_index, node.index, node.node_type, content, locked=True, source="manual_review", sync_chapter=False)
            existing_texts = self.state.setdefault("chapter_texts", [])
            while len(existing_texts) < chapter_index:
                existing_texts.append("")
            existing = str(existing_texts[chapter_index - 1] or "")
            existing_texts[chapter_index - 1] = f"{existing}{chr(10) + chr(10) if existing else ''}{content}"
            self.state["baseline_texts"] = list(existing_texts)
            self.state["progress"]["total_words"] = sum(len(str(text or "")) for text in existing_texts)
            save_chapter_text(self.state["novel_id"], chapter_index, existing_texts[chapter_index - 1])
            return node.model_copy(update={"content": content})
        return node

    def _build_generation_logic(self, node: ChapterNode, questions: Any, context: Any) -> str:
        context_brief = ""
        if hasattr(context, "human_prompt"):
            context_brief = str(context.human_prompt())
        elif isinstance(context, dict):
            context_brief = str(context.get("memory_brief") or context.get("selected_context") or context)[:500]
        return (
            f"本节点要写 {node.node_type}：触发点是“{node.trigger_point}”，情绪目标是“{node.emotion_purpose}”，"
            f"读者期待是“{node.reader_expectation}”。写作四问：{questions.model_dump() if hasattr(questions, 'model_dump') else questions}。"
            f"参考上下文：{context_brief[:500]}"
        )

    def _notify_fallback_if_needed(self, payload: Any) -> None:
        notice = fallback_notice(payload)
        if notice:
            self._notify("llm_fallback_used", notice)

    def _rewrite_with_feedback(self, chapter_index: int, review_data: dict[str, Any]) -> None:
        warnings = []
        warnings.extend(review_data.get("rhythm", {}).get("warnings", []))
        warnings.extend(review_data.get("information_gap", {}).get("suggestions", []))
        warnings.extend(review_data.get("outline_check", {}).get("issues", []))
        self._notify("error", {"message": f"chapter {chapter_index} quality below threshold, rewriting with feedback: {warnings}", "fatal": False})

    def _get_llm(self) -> Callable[[str, str, bool], str]:
        config = self.state.get("llm_config", {})

        def llm_call(prompt: str, system_prompt: str = "", json_mode: bool = False) -> str:
            return call_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                json_mode=json_mode,
                api_key=config.get("api_key") or None,
                base_url=config.get("api_base_url") or None,
                model=config.get("model") or None,
            )

        return llm_call

    def _wait_if_paused(self) -> None:
        while self.state["status"] == "paused":
            time.sleep(1)

    def _persist_state(self) -> None:
        try:
            save_daemon_state(self.get_state())
        except Exception as exc:
            with self.state_lock:
                self.state["errors"].append(f"state persistence error: {exc}")

    def _notify(self, event_type: str, data: dict[str, Any]) -> None:
        state_snapshot = self.get_state()
        event = {"type": event_type, "data": data, "state": state_snapshot}
        self._persist_state()
        for listener in list(self.listeners):
            try:
                listener(event)
            except Exception as exc:
                with self.state_lock:
                    self.state["errors"].append(f"listener error: {exc}")
