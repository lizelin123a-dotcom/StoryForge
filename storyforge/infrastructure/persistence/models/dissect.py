from datetime import datetime

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
