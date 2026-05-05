from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from storyforge.application.audit.services.outline_check_service import check_chapter_outline
from storyforge.application.planner.services.act_planner import generate_act_plans
from storyforge.application.planner.services.chapter_outliner import generate_chapter_outline
from storyforge.application.planner.services.macro_planner import generate_macro_outline
from storyforge.application.writer.services.consistency_checker import check_node_consistency
from storyforge.application.writer.services.node_generator import generate_node_content
from storyforge.domain.node.node import ChapterNode
from storyforge.infrastructure.persistence.database import SessionLocal, init_db
from storyforge.infrastructure.persistence.models.novel_writing import ActPlanModel, ChapterOutlineModel, MacroOutlineModel
from storyforge.infrastructure.persistence.repository import CRUDRepository

router = APIRouter(tags=["planner-writer"])


class MacroOutlineRequest(BaseModel):
    title: str
    world_setting: str
    characters: str
    target_word_count: int
    genre: str
    dissect_source_id: str | None = None


class ChapterOutlineRequest(BaseModel):
    act_index: int
    chapter_index: int
    chapter_function: str


class GenerateNodeRequest(BaseModel):
    node: ChapterNode
    context: dict[str, Any] = {}


class ConsistencyRequest(BaseModel):
    nodes: list[ChapterNode]


@router.post("/api/v1/planner/macro-outline")
def macro_outline(request: MacroOutlineRequest) -> dict[str, Any]:
    init_db()
    outline = generate_macro_outline(
        title=request.title,
        world_setting=request.world_setting,
        characters=request.characters,
        target_word_count=request.target_word_count,
        genre=request.genre,
    )
    outline_id = str(uuid4())
    outline["id"] = outline_id
    with SessionLocal() as session:
        CRUDRepository(session, MacroOutlineModel).create({"id": outline_id, "outline_json": outline})
    return outline


@router.post("/api/v1/planner/{outline_id}/act-plans")
def act_plans(outline_id: str) -> dict[str, Any]:
    with SessionLocal() as session:
        outline_row = CRUDRepository(session, MacroOutlineModel).get(outline_id)
        if outline_row is None:
            raise HTTPException(status_code=404, detail="macro outline not found")
        outline = dict(outline_row.outline_json)
        acts = generate_act_plans(outline)
        act_repo = CRUDRepository(session, ActPlanModel)
        existing = _get_act_plan_row(session, outline_id)
        payload = {"id": existing.id if existing else str(uuid4()), "outline_id": outline_id, "act_plans_json": acts}
        if existing is None:
            act_repo.create(payload)
        else:
            act_repo.update(existing.id, payload)
        return {"outline_id": outline_id, "act_plans": acts}


@router.post("/api/v1/planner/act/{act_index}/chapter-outline")
def chapter_outline(act_index: int, request: ChapterOutlineRequest) -> dict[str, Any]:
    with SessionLocal() as session:
        act_plan = _find_act_plan(session, act_index)
        nodes = generate_chapter_outline(act_plan, request.chapter_index, request.chapter_function)
        chapter_id = f"chapter-{request.chapter_index}"
        outline_json = [node.model_dump() for node in nodes]
        repo = CRUDRepository(session, ChapterOutlineModel)
        existing = _get_chapter_outline_row(session, chapter_id)
        payload = {"id": existing.id if existing else str(uuid4()), "chapter_id": chapter_id, "outline_json": outline_json}
        if existing is None:
            repo.create(payload)
        else:
            repo.update(existing.id, payload)
        return {"chapter_id": chapter_id, "nodes": outline_json}


@router.post("/api/v1/planner/chapter-outline/{chapter_id}/check")
def check_outline(chapter_id: str) -> dict[str, Any]:
    with SessionLocal() as session:
        row = _get_chapter_outline_row(session, chapter_id)
        if row is None:
            raise HTTPException(status_code=404, detail="chapter outline not found")
        nodes = [ChapterNode(**node) for node in row.outline_json]
        return check_chapter_outline(nodes)


@router.post("/api/v1/writer/generate-node")
def generate_node(request: GenerateNodeRequest) -> dict[str, Any]:
    try:
        node = generate_node_content(request.node, request.context)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"node generation failed: {exc}") from exc
    return node.model_dump()


@router.post("/api/v1/writer/check-consistency")
def check_consistency(request: ConsistencyRequest) -> dict[str, Any]:
    return check_node_consistency(request.nodes)


def _get_act_plan_row(session, outline_id: str) -> ActPlanModel | None:
    return session.query(ActPlanModel).filter(ActPlanModel.outline_id == outline_id).first()


def _get_chapter_outline_row(session, chapter_id: str) -> ChapterOutlineModel | None:
    return session.query(ChapterOutlineModel).filter(ChapterOutlineModel.chapter_id == chapter_id).first()


def _find_act_plan(session, act_index: int) -> dict[str, Any]:
    for row in session.query(ActPlanModel).all():
        for act in row.act_plans_json:
            if int(act.get("index", -1)) == act_index:
                return act
    return {"index": act_index, "name": f"第{act_index}幕", "function": "推进主线", "core_conflict": "主角目标与阻碍冲突", "chapters": []}
