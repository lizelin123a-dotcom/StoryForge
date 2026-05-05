from pathlib import Path

files: dict[str, str] = {
    "storyforge/__init__.py": "",
    "storyforge/__main__.py": """from uvicorn import run


def main() -> None:
    run("storyforge.interfaces.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
""",
    "storyforge/requirements.txt": """fastapi>=0.110.0
uvicorn[standard]>=0.27.0
SQLAlchemy>=2.0.0
aiosqlite>=0.19.0
pydantic>=2.0.0
httpx>=0.26.0
python-dotenv>=1.0.0
""",
    "storyforge/.env.example": """OPENAI_API_KEY=
DATABASE_URL=sqlite:///./storyforge.db
LOG_LEVEL=INFO
""",
    "storyforge/domain/__init__.py": "",
    "storyforge/domain/dissect/__init__.py": """from .source_novel import SourceNovel
from .dissected_chapter import DissectedChapter, ShuangPoint, UnitStructure
from .replacement_table import ReplacementTable

__all__ = [
    "SourceNovel",
    "DissectedChapter",
    "ShuangPoint",
    "UnitStructure",
    "ReplacementTable",
]
""",
    "storyforge/domain/dissect/source_novel.py": """from datetime import datetime

from pydantic import BaseModel, Field


class SourceNovel(BaseModel):
    id: str
    title: str
    author: str
    genre: str
    word_count: int = Field(ge=0)
    raw_text: str
    created_at: datetime
""",
    "storyforge/domain/dissect/dissected_chapter.py": """from pydantic import BaseModel, Field


class ShuangPoint(BaseModel):
    position_start: int = Field(ge=0)
    position_end: int = Field(ge=0)
    shuang_type: str
    pre_emotion: str
    post_emotion: str
    setup_word_count: int = Field(ge=0)
    burst_word_count: int = Field(ge=0)
    info_gap_level: str
    involved_interests: list[str]


class UnitStructure(BaseModel):
    obstacle: str
    side_support: str
    harvest: str
    breakthrough: str
    word_count: int = Field(ge=0)


class DissectedChapter(BaseModel):
    id: str
    source_novel_id: str
    chapter_index: int = Field(ge=0)
    title: str
    shuang_points: list[ShuangPoint]
    emotional_curve: dict
    structure_summary: str
    core_conflict: str
""",
    "storyforge/domain/dissect/replacement_table.py": """from pydantic import BaseModel


class ReplacementTable(BaseModel):
    world_setting_replace: dict
    golden_finger_replace: dict
    power_system_replace: dict
    conflict_system_replace: dict
    character_replace: dict
""",
    "storyforge/domain/node/__init__.py": """from .node import ChapterNode, WritingFourQuestions

__all__ = ["ChapterNode", "WritingFourQuestions"]
""",
    "storyforge/domain/node/node.py": """from typing import Optional

from pydantic import BaseModel, Field


class ChapterNode(BaseModel):
    id: str
    chapter_id: str
    index: int = Field(ge=0)
    trigger_point: str
    emotion_purpose: str
    reader_expectation: str
    node_type: str
    expected_word_count: int = Field(ge=0)
    content: Optional[str] = None


class WritingFourQuestions(BaseModel):
    emotion: str
    character_state: str
    reader_expectation: str
    shuang_type: str
""",
    "storyforge/domain/material/__init__.py": """from .material_bank import MaterialBank
from .character_card import CharacterCard

__all__ = ["MaterialBank", "CharacterCard"]
""",
    "storyforge/domain/material/material_bank.py": """from pydantic import BaseModel


class MaterialBank(BaseModel):
    id: str
    name: str
    items: dict
""",
    "storyforge/domain/material/character_card.py": """from pydantic import BaseModel


class CharacterCard(BaseModel):
    name: str
    identity: str
    appearance: str
    personality_tags: list[str]
    ability: str
    background: str
    current_goal: str
    relationships: list[str]
    conflict_points: list[str]
    growth_arc: str
""",
    "storyforge/domain/shared/__init__.py": """from .emotion import Emotion
from .conflict import Conflict

__all__ = ["Emotion", "Conflict"]
""",
    "storyforge/domain/shared/emotion.py": """from enum import Enum


class Emotion(str, Enum):
    CURIOSITY = "濂藉"
    TENSION = "绱у紶"
    SUFFOCATED = "鎲嬪眻"
    SATISFACTION_BURST = "鐖?
    SATISFIED = "婊¤冻"
    EXPECTATION = "鏈熷緟"
    SHOCK = "闇囨捈"
    ANGER = "鎰ゆ€?
    ANXIETY = "鐒﹁檻"
    AFTERTASTE = "鍥炲懗"
""",
    "storyforge/domain/shared/conflict.py": """from pydantic import BaseModel


class Conflict(BaseModel):
    conflict_type: str
    description: str
    involved_interests: list[str]
    status: str
    evolution_path: list[str]
""",
    "storyforge/domain/novel/__init__.py": """from .novel import Novel
from .chapter import Chapter
from .volume import Volume

__all__ = ["Novel", "Chapter", "Volume"]
""",
    "storyforge/domain/novel/novel.py": """from datetime import datetime

from pydantic import BaseModel, Field


class Novel(BaseModel):
    id: str
    title: str
    author: str
    genre: str
    summary: str = ""
    word_count: int = Field(default=0, ge=0)
    created_at: datetime
    updated_at: datetime | None = None
""",
    "storyforge/domain/novel/chapter.py": """from pydantic import BaseModel, Field


class Chapter(BaseModel):
    id: str
    novel_id: str
    volume_id: str | None = None
    index: int = Field(ge=0)
    title: str
    content: str = ""
    word_count: int = Field(default=0, ge=0)
""",
    "storyforge/domain/novel/volume.py": """from pydantic import BaseModel, Field


class Volume(BaseModel):
    id: str
    novel_id: str
    index: int = Field(ge=0)
    title: str
    summary: str = ""
""",
    "storyforge/application/__init__.py": "",
    "storyforge/application/dissect/__init__.py": "",
    "storyforge/application/dissect/services/__init__.py": "",
    "storyforge/application/planner/__init__.py": "",
    "storyforge/application/writer/__init__.py": "",
    "storyforge/application/analyst/__init__.py": "",
    "storyforge/application/audit/__init__.py": "",
    "storyforge/infrastructure/__init__.py": "",
    "storyforge/infrastructure/ai/__init__.py": "",
    "storyforge/infrastructure/persistence/__init__.py": """from .database import Base, SessionLocal, engine, init_db
from .repository import CRUDRepository

__all__ = ["Base", "SessionLocal", "engine", "init_db", "CRUDRepository"]
""",
    "storyforge/infrastructure/persistence/database.py": """import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./storyforge.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
""",
    "storyforge/infrastructure/persistence/repository.py": """from typing import Generic, TypeVar

from sqlalchemy.orm import Session

from .database import Base

ModelT = TypeVar("ModelT", bound=Base)


class CRUDRepository(Generic[ModelT]):
    def __init__(self, session: Session, model: type[ModelT]) -> None:
        self.session = session
        self.model = model

    def get(self, entity_id: str) -> ModelT | None:
        return self.session.get(self.model, entity_id)

    def list(self, offset: int = 0, limit: int = 100) -> list[ModelT]:
        return list(self.session.query(self.model).offset(offset).limit(limit).all())

    def create(self, data: dict) -> ModelT:
        entity = self.model(**data)
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def update(self, entity_id: str, data: dict) -> ModelT | None:
        entity = self.get(entity_id)
        if entity is None:
            return None
        for key, value in data.items():
            setattr(entity, key, value)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def delete(self, entity_id: str) -> bool:
        entity = self.get(entity_id)
        if entity is None:
            return False
        self.session.delete(entity)
        self.session.commit()
        return True
""",
    "storyforge/interfaces/__init__.py": "",
    "storyforge/interfaces/main.py": """from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from storyforge.infrastructure.persistence import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(title="StoryForge", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
""",
    "storyforge/interfaces/api/__init__.py": "",
    "storyforge/interfaces/api/v1/__init__.py": "",
}

for path, content in files.items():
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")

print(f"Wrote {len(files)} base files")
