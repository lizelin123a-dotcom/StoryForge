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
    segment_function: str = ""
    what_to_write: str = ""
    ends_with: str = ""
    characters: list[str] = Field(default_factory=list)
    micro_payoff: str = ""


class WritingFourQuestions(BaseModel):
    emotion: str
    character_state: str
    reader_expectation: str
    shuang_type: str
