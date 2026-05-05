from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from storyforge.application.cocreation.service import next_cocreation_turn
from storyforge.infrastructure.knowledge import list_editor_skills

router = APIRouter(tags=["cocreation"])


class CocreationMessage(BaseModel):
    role: str
    content: str


class CocreationTurnRequest(BaseModel):
    logline: str = ""
    messages: list[CocreationMessage] = Field(default_factory=list)
    assets: dict[str, Any] = Field(default_factory=dict)
    writing_context: dict[str, Any] = Field(default_factory=dict)
    skill_ids: list[str] = Field(default_factory=list)
    api_key: str = ""
    api_base_url: str = ""
    model: str = ""


@router.get("/api/v1/cocreation/skills")
def cocreation_skills() -> dict[str, Any]:
    return {"items": [{k: v for k, v in item.items() if k != "content"} for item in list_editor_skills()]}


@router.post("/api/v1/cocreation/turn")
def cocreation_turn(request: CocreationTurnRequest) -> dict[str, Any]:
    return next_cocreation_turn(
        logline=request.logline,
        messages=[item.model_dump() for item in request.messages],
        assets=request.assets,
        writing_context=request.writing_context,
        skill_ids=request.skill_ids,
        api_key=request.api_key,
        api_base_url=request.api_base_url,
        model=request.model,
    )
