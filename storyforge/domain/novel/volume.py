from pydantic import BaseModel, Field


class Volume(BaseModel):
    id: str
    novel_id: str
    index: int = Field(ge=0)
    title: str
    summary: str = ""
