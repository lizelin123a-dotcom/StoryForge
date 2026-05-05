from pathlib import Path

files: dict[str, str] = {
    "storyforge/infrastructure/persistence/models/__init__.py": """from .novel import ChapterModel, NovelModel, VolumeModel
from .dissect import (
    DissectedChapterModel,
    ReplacementTableModel,
    ShuangPointModel,
    SourceNovelModel,
    UnitStructureModel,
)
from .material import CharacterCardModel, MaterialBankModel
from .node import ChapterNodeModel, WritingFourQuestionsModel
from .shared import ConflictModel

__all__ = [
    "ChapterModel",
    "NovelModel",
    "VolumeModel",
    "DissectedChapterModel",
    "ReplacementTableModel",
    "ShuangPointModel",
    "SourceNovelModel",
    "UnitStructureModel",
    "CharacterCardModel",
    "MaterialBankModel",
    "ChapterNodeModel",
    "WritingFourQuestionsModel",
    "ConflictModel",
]
""",
    "storyforge/infrastructure/persistence/models/novel.py": """from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class NovelModel(Base):
    __tablename__ = "novels"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False)
    genre: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="")
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class VolumeModel(Base):
    __tablename__ = "volumes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    novel_id: Mapped[str] = mapped_column(String, ForeignKey("novels.id"), nullable=False)
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="")


class ChapterModel(Base):
    __tablename__ = "chapters"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    novel_id: Mapped[str] = mapped_column(String, ForeignKey("novels.id"), nullable=False)
    volume_id: Mapped[str | None] = mapped_column(String, ForeignKey("volumes.id"), nullable=True)
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")
    word_count: Mapped[int] = mapped_column(Integer, default=0)
""",
    "storyforge/infrastructure/persistence/models/dissect.py": """from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class SourceNovelModel(Base):
    __tablename__ = "source_novels"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False)
    genre: Mapped[str] = mapped_column(String, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class DissectedChapterModel(Base):
    __tablename__ = "dissected_chapters"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    source_novel_id: Mapped[str] = mapped_column(String, ForeignKey("source_novels.id"), nullable=False)
    chapter_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    shuang_points: Mapped[list] = mapped_column(JSON, default=list)
    emotional_curve: Mapped[dict] = mapped_column(JSON, default=dict)
    structure_summary: Mapped[str] = mapped_column(Text, nullable=False)
    core_conflict: Mapped[str] = mapped_column(Text, nullable=False)


class ShuangPointModel(Base):
    __tablename__ = "shuang_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dissected_chapter_id: Mapped[str | None] = mapped_column(String, ForeignKey("dissected_chapters.id"), nullable=True)
    position_start: Mapped[int] = mapped_column(Integer, nullable=False)
    position_end: Mapped[int] = mapped_column(Integer, nullable=False)
    shuang_type: Mapped[str] = mapped_column(String, nullable=False)
    pre_emotion: Mapped[str] = mapped_column(String, nullable=False)
    post_emotion: Mapped[str] = mapped_column(String, nullable=False)
    setup_word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    burst_word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    info_gap_level: Mapped[str] = mapped_column(String, nullable=False)
    involved_interests: Mapped[list[str]] = mapped_column(JSON, default=list)


class ReplacementTableModel(Base):
    __tablename__ = "replacement_tables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    world_setting_replace: Mapped[dict] = mapped_column(JSON, default=dict)
    golden_finger_replace: Mapped[dict] = mapped_column(JSON, default=dict)
    power_system_replace: Mapped[dict] = mapped_column(JSON, default=dict)
    conflict_system_replace: Mapped[dict] = mapped_column(JSON, default=dict)
    character_replace: Mapped[dict] = mapped_column(JSON, default=dict)


class UnitStructureModel(Base):
    __tablename__ = "unit_structures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    obstacle: Mapped[str] = mapped_column(Text, nullable=False)
    side_support: Mapped[str] = mapped_column(Text, nullable=False)
    harvest: Mapped[str] = mapped_column(Text, nullable=False)
    breakthrough: Mapped[str] = mapped_column(Text, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)
""",
    "storyforge/infrastructure/persistence/models/node.py": """from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class ChapterNodeModel(Base):
    __tablename__ = "chapter_nodes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    chapter_id: Mapped[str] = mapped_column(String, nullable=False)
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    trigger_point: Mapped[str] = mapped_column(Text, nullable=False)
    emotion_purpose: Mapped[str] = mapped_column(String, nullable=False)
    reader_expectation: Mapped[str] = mapped_column(Text, nullable=False)
    node_type: Mapped[str] = mapped_column(String, nullable=False)
    expected_word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)


class WritingFourQuestionsModel(Base):
    __tablename__ = "writing_four_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    emotion: Mapped[str] = mapped_column(String, nullable=False)
    character_state: Mapped[str] = mapped_column(Text, nullable=False)
    reader_expectation: Mapped[str] = mapped_column(Text, nullable=False)
    shuang_type: Mapped[str] = mapped_column(String, nullable=False)
""",
    "storyforge/infrastructure/persistence/models/material.py": """from sqlalchemy import JSON, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class MaterialBankModel(Base):
    __tablename__ = "material_banks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    items: Mapped[dict] = mapped_column(JSON, default=dict)


class CharacterCardModel(Base):
    __tablename__ = "character_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    identity: Mapped[str] = mapped_column(String, nullable=False)
    appearance: Mapped[str] = mapped_column(Text, nullable=False)
    personality_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    ability: Mapped[str] = mapped_column(Text, nullable=False)
    background: Mapped[str] = mapped_column(Text, nullable=False)
    current_goal: Mapped[str] = mapped_column(Text, nullable=False)
    relationships: Mapped[list[str]] = mapped_column(JSON, default=list)
    conflict_points: Mapped[list[str]] = mapped_column(JSON, default=list)
    growth_arc: Mapped[str] = mapped_column(Text, nullable=False)
""",
    "storyforge/infrastructure/persistence/models/shared.py": """from sqlalchemy import JSON, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class ConflictModel(Base):
    __tablename__ = "conflicts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conflict_type: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    involved_interests: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String, nullable=False)
    evolution_path: Mapped[list[str]] = mapped_column(JSON, default=list)
""",
}

for path, content in files.items():
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")

print(f"Wrote {len(files)} ORM files")
