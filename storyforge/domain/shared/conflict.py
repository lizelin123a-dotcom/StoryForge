from pydantic import BaseModel


class Conflict(BaseModel):
    conflict_type: str
    description: str
    involved_interests: list[str]
    status: str
    evolution_path: list[str]
