from pydantic import BaseModel


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
