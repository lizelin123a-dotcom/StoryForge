from datetime import datetime

from pydantic import BaseModel, Field


class SourceNovel(BaseModel):
    id: str
    title: str
    author: str
    genre: str
    word_count: int = Field(ge=0)
    raw_text: str
    created_at: datetime
