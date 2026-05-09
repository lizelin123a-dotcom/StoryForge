from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class MacroOutlineModel(Base):
    __tablename__ = "macro_outlines"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    outline_json: Mapped[dict] = mapped_column(JSON, nullable=False)


class ActPlanModel(Base):
    __tablename__ = "act_plans"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    outline_id: Mapped[str] = mapped_column(String, nullable=False)
    act_plans_json: Mapped[list] = mapped_column(JSON, nullable=False)


class ChapterOutlineModel(Base):
    __tablename__ = "chapter_outlines"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    chapter_id: Mapped[str] = mapped_column(String, nullable=False)
    outline_json: Mapped[dict] = mapped_column(JSON, nullable=False)


class ChapterArchiveModel(Base):
    __tablename__ = "chapter_archives"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    novel_id: Mapped[str] = mapped_column(String, ForeignKey("novels.id"), nullable=False)
    chapter_id: Mapped[str] = mapped_column(String, nullable=False)
    chapter_index: Mapped[int] = mapped_column(Integer, nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="")
    review_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    memory_delta_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class CurrentFocusModel(Base):
    __tablename__ = "current_focus"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    novel_id: Mapped[str] = mapped_column(String, ForeignKey("novels.id"), nullable=False)
    priority: Mapped[str] = mapped_column(Text, default="")
    active_subplots_json: Mapped[list] = mapped_column(JSON, nullable=False)
    hooks_to_mention_json: Mapped[list] = mapped_column(JSON, nullable=False)
    pacing_intent: Mapped[str] = mapped_column(Text, default="")
    constraints_json: Mapped[list] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class ChapterSpanModel(Base):
    __tablename__ = "chapter_spans"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    novel_id: Mapped[str] = mapped_column(String, ForeignKey("novels.id"), nullable=False)
    chapter_id: Mapped[str] = mapped_column(String, nullable=False)
    node_id: Mapped[str] = mapped_column(String, nullable=False)
    start_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    end_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    outline_snapshot: Mapped[str] = mapped_column(Text, default="")
    draft_snapshot: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
