from datetime import datetime

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
