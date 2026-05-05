from typing import Optional

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
