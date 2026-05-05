from sqlalchemy import Integer, String, Text
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
