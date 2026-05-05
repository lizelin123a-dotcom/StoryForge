from pydantic import BaseModel, Field


class Chapter(BaseModel):
    id: str
    novel_id: str
    volume_id: str | None = None
    index: int = Field(ge=0)
    title: str
    content: str = ""
    word_count: int = Field(default=0, ge=0)
