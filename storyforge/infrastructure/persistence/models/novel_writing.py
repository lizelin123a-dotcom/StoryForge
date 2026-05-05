from sqlalchemy import JSON, String
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
    outline_json: Mapped[list] = mapped_column(JSON, nullable=False)
