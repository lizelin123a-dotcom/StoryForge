from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from storyforge.application.dissect.services.first_pass_service import run_first_pass
from storyforge.application.dissect.services.material_integration_service import integrate_material_bank
from storyforge.application.dissect.services.replacement_service import generate_replacement_table
from storyforge.application.dissect.services.second_pass_service import run_second_pass
from storyforge.application.dissect.services.third_pass_service import run_third_pass
from storyforge.domain.dissect.dissected_chapter import DissectedChapter, UnitStructure
from storyforge.domain.dissect.replacement_table import ReplacementTable
from storyforge.domain.dissect.source_novel import SourceNovel
from storyforge.domain.material.material_bank import MaterialBank
from storyforge.infrastructure.persistence.database import SessionLocal, init_db
from storyforge.infrastructure.persistence.models.dissect import DissectedChapterModel, ReplacementTableModel, SourceNovelModel, UnitStructureModel
from storyforge.infrastructure.persistence.models.material import MaterialBankModel
from storyforge.infrastructure.persistence.repository import CRUDRepository

router = APIRouter(prefix="/api/v1/dissect", tags=["dissect"])


class UploadRequest(BaseModel):
    title: str
    author: str
    genre: str
    raw_text: str = Field(min_length=1)


class ReplacementRequest(BaseModel):
    world_setting: str
    golden_finger: str
    power_system: str
    conflict_system: str
    character_settings: str


@router.post("/upload")
def upload_source_novel(request: UploadRequest) -> dict[str, str]:
    init_db()
    source_id = str(uuid4())
    with SessionLocal() as session:
        CRUDRepository(session, SourceNovelModel).create({
            "id": source_id,
            "title": request.title,
            "author": request.author,
            "genre": request.genre,
            "word_count": len(request.raw_text),
            "raw_text": request.raw_text,
            "created_at": datetime.utcnow(),
        })
    return {"id": source_id}


@router.post("/{source_id}/first-pass")
def first_pass(source_id: str) -> dict[str, list[dict[str, Any]]]:
    with SessionLocal() as session:
        source = _get_source(session, source_id)
        try:
            chapters = run_first_pass(source)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"first-pass LLM failed: {exc}") from exc
        _replace_dissected_chapters(session, source_id, "first", chapters)
        return {"dissected_chapters": [chapter.model_dump() for chapter in chapters]}


@router.post("/{source_id}/second-pass")
def second_pass(source_id: str) -> dict[str, list[dict[str, Any]]]:
    with SessionLocal() as session:
        source = _get_source(session, source_id)
        chapters = _get_first_pass(session, source_id)
        try:
            enhanced = run_second_pass(source.raw_text, chapters)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"second-pass LLM failed: {exc}") from exc
        _replace_dissected_chapters(session, source_id, "second", enhanced)
        return {"dissected_chapters": [chapter.model_dump() for chapter in enhanced]}


@router.post("/{source_id}/third-pass")
def third_pass(source_id: str) -> dict[str, list[dict[str, Any]]]:
    with SessionLocal() as session:
        source = _get_source(session, source_id)
        chapters = _load_dissected_chapters(session, source_id, "second") or _get_first_pass(session, source_id)
        try:
            units = run_third_pass(source.raw_text, chapters)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"third-pass LLM failed: {exc}") from exc
        _replace_unit_structures(session, source_id, units)
        return {"unit_structures": [unit.model_dump() for unit in units]}


@router.get("/{source_id}/result")
def result(source_id: str) -> dict[str, Any]:
    with SessionLocal() as session:
        source = _get_source(session, source_id)
        replacement = _load_replacement_table(session, source_id)
        material = _load_material_bank(session, source_id)
        return {
            "source_novel": source.model_dump(),
            "first_pass": [chapter.model_dump() for chapter in _load_dissected_chapters(session, source_id, "first")],
            "second_pass": [chapter.model_dump() for chapter in _load_dissected_chapters(session, source_id, "second")],
            "third_pass": [unit.model_dump() for unit in _load_unit_structures(session, source_id)],
            "replacement_table": replacement.model_dump() if replacement else None,
            "material_bank": material.model_dump() if material else None,
        }


@router.post("/{source_id}/generate-replacement")
def generate_replacement(source_id: str, request: ReplacementRequest) -> dict[str, Any]:
    with SessionLocal() as session:
        _get_source(session, source_id)
        chapters = _load_dissected_chapters(session, source_id, "second") or _load_dissected_chapters(session, source_id, "first")
        benchmark_summary = "\n".join(
            f"{chapter.title}: {chapter.structure_summary}; 核心矛盾: {chapter.core_conflict}"
            for chapter in chapters
        )
        try:
            table = generate_replacement_table(
                benchmark_summary=benchmark_summary,
                world_setting=request.world_setting,
                golden_finger=request.golden_finger,
                power_system=request.power_system,
                conflict_system=request.conflict_system,
                character_settings=request.character_settings,
            )
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"replacement LLM failed: {exc}") from exc
        _replace_replacement_table(session, source_id, table)
        return table.model_dump()


@router.post("/{source_id}/integrate-material")
def integrate_material(source_id: str) -> dict[str, Any]:
    with SessionLocal() as session:
        _get_source(session, source_id)
        chapters = _load_dissected_chapters(session, source_id, "second") or _get_first_pass(session, source_id)
        units = _load_unit_structures(session, source_id)
        try:
            bank = integrate_material_bank(source_id, chapters, units)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"material integration LLM failed: {exc}") from exc
        _replace_material_bank(session, source_id, bank)
        return bank.model_dump()


@router.get("/{source_id}/shuang-analysis")
def shuang_analysis(source_id: str) -> dict[str, Any]:
    with SessionLocal() as session:
        chapters = _load_dissected_chapters(session, source_id, "second") or _get_first_pass(session, source_id)
        frequency: dict[str, int] = {}
        rhythm_notes: list[str] = []
        for chapter in chapters:
            for point in chapter.shuang_points:
                frequency[point.shuang_type] = frequency.get(point.shuang_type, 0) + 1
            second = chapter.emotional_curve.get("second_pass", {})
            for item in second.get("shuang_points_detail", []):
                detail = item.get("second_pass", {}) if isinstance(item, dict) else {}
                rhythm = detail.get("rhythm_pattern")
                if rhythm:
                    rhythm_notes.append(str(rhythm))
        return {
            "frequency": frequency,
            "total": sum(frequency.values()),
            "rhythm_summary": rhythm_notes or ["尚未执行第二遍，暂无节奏模式摘要"],
        }


def _get_source(session: Session, source_id: str) -> SourceNovel:
    init_db()
    source = CRUDRepository(session, SourceNovelModel).get(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="source novel not found")
    return SourceNovel(
        id=source.id,
        title=source.title,
        author=source.author,
        genre=source.genre,
        word_count=source.word_count,
        raw_text=source.raw_text,
        created_at=source.created_at,
    )


def _get_first_pass(session: Session, source_id: str) -> list[DissectedChapter]:
    chapters = _load_dissected_chapters(session, source_id, "first")
    if not chapters:
        raise HTTPException(status_code=404, detail="first-pass result not found")
    return chapters


def _load_dissected_chapters(session: Session, source_id: str, pass_name: str) -> list[DissectedChapter]:
    prefix = f"{source_id}:{pass_name}:"
    rows = (
        session.query(DissectedChapterModel)
        .filter(DissectedChapterModel.source_novel_id == source_id, DissectedChapterModel.id.like(f"{prefix}%"))
        .order_by(DissectedChapterModel.chapter_index.asc())
        .all()
    )
    return [
        DissectedChapter(
            id=_strip_pass_prefix(row.id, source_id, pass_name),
            source_novel_id=row.source_novel_id,
            chapter_index=row.chapter_index,
            title=row.title,
            shuang_points=row.shuang_points or [],
            emotional_curve=row.emotional_curve or {},
            structure_summary=row.structure_summary,
            core_conflict=row.core_conflict,
        )
        for row in rows
    ]


def _replace_dissected_chapters(session: Session, source_id: str, pass_name: str, chapters: list[DissectedChapter]) -> None:
    prefix = f"{source_id}:{pass_name}:"
    session.query(DissectedChapterModel).filter(DissectedChapterModel.source_novel_id == source_id, DissectedChapterModel.id.like(f"{prefix}%")).delete(synchronize_session=False)
    repo = CRUDRepository(session, DissectedChapterModel)
    for chapter in chapters:
        data = chapter.model_dump()
        repo.create({
            "id": f"{prefix}{data['id']}",
            "source_novel_id": source_id,
            "chapter_index": data["chapter_index"],
            "title": data["title"],
            "shuang_points": data.get("shuang_points", []),
            "emotional_curve": data.get("emotional_curve", {}),
            "structure_summary": data.get("structure_summary", ""),
            "core_conflict": data.get("core_conflict", ""),
        })


def _strip_pass_prefix(row_id: str, source_id: str, pass_name: str) -> str:
    prefix = f"{source_id}:{pass_name}:"
    return row_id[len(prefix):] if row_id.startswith(prefix) else row_id


def _load_unit_structures(session: Session, source_id: str) -> list[UnitStructure]:
    rows = session.query(UnitStructureModel).filter(UnitStructureModel.obstacle.like(f"[{source_id}]%")) .order_by(UnitStructureModel.id.asc()).all()
    return [
        UnitStructure(
            obstacle=_strip_source_marker(row.obstacle, source_id),
            side_support=row.side_support,
            harvest=row.harvest,
            breakthrough=row.breakthrough,
            word_count=row.word_count,
        )
        for row in rows
    ]


def _replace_unit_structures(session: Session, source_id: str, units: list[UnitStructure]) -> None:
    session.query(UnitStructureModel).filter(UnitStructureModel.obstacle.like(f"[{source_id}]%")).delete(synchronize_session=False)
    repo = CRUDRepository(session, UnitStructureModel)
    for unit in units:
        data = unit.model_dump()
        repo.create({
            "obstacle": f"[{source_id}]{data.get('obstacle', '')}",
            "side_support": data.get("side_support", ""),
            "harvest": data.get("harvest", ""),
            "breakthrough": data.get("breakthrough", ""),
            "word_count": data.get("word_count", 0),
        })


def _strip_source_marker(value: str, source_id: str) -> str:
    marker = f"[{source_id}]"
    return value[len(marker):] if value.startswith(marker) else value


def _load_replacement_table(session: Session, source_id: str) -> ReplacementTable | None:
    row = session.get(ReplacementTableModel, _replacement_id(source_id))
    if row is None:
        return None
    return ReplacementTable(
        world_setting_replace=row.world_setting_replace or {},
        golden_finger_replace=row.golden_finger_replace or {},
        power_system_replace=row.power_system_replace or {},
        conflict_system_replace=row.conflict_system_replace or {},
        character_replace=row.character_replace or {},
    )


def _replace_replacement_table(session: Session, source_id: str, table: ReplacementTable) -> None:
    data = table.model_dump()
    existing = session.get(ReplacementTableModel, _replacement_id(source_id))
    payload = {
        "world_setting_replace": data.get("world_setting_replace", {}),
        "golden_finger_replace": data.get("golden_finger_replace", {}),
        "power_system_replace": data.get("power_system_replace", {}),
        "conflict_system_replace": data.get("conflict_system_replace", {}),
        "character_replace": data.get("character_replace", {}),
    }
    if existing is None:
        existing = ReplacementTableModel(id=_replacement_id(source_id), **payload)
        session.add(existing)
    else:
        for key, value in payload.items():
            setattr(existing, key, value)
    session.commit()


def _replacement_id(source_id: str) -> int:
    return int(source_id.replace("-", "")[:12], 16) % 2_147_483_647


def _load_material_bank(session: Session, source_id: str) -> MaterialBank | None:
    row = CRUDRepository(session, MaterialBankModel).get(source_id)
    if row is None:
        return None
    return MaterialBank(id=row.id, name=row.name, items=row.items or {})


def _replace_material_bank(session: Session, source_id: str, bank: MaterialBank) -> None:
    repo = CRUDRepository(session, MaterialBankModel)
    data = bank.model_dump()
    payload = {"id": source_id, "name": data.get("name", f"{source_id} material bank"), "items": data.get("items", {})}
    if repo.get(source_id) is None:
        repo.create(payload)
    else:
        repo.update(source_id, payload)
