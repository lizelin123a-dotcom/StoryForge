from pydantic import BaseModel, Field


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
