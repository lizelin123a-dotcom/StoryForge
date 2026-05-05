from sqlalchemy import JSON, Integer, String, Text
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
