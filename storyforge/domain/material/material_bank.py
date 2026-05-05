from pydantic import BaseModel


class MaterialBank(BaseModel):
    id: str
    name: str
    items: dict
