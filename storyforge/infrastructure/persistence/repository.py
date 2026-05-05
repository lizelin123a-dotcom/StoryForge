from typing import Generic, TypeVar

from sqlalchemy.orm import Session

from .database import Base

ModelT = TypeVar("ModelT", bound=Base)


class CRUDRepository(Generic[ModelT]):
    def __init__(self, session: Session, model: type[ModelT]) -> None:
        self.session = session
        self.model = model

    def get(self, entity_id: str) -> ModelT | None:
        return self.session.get(self.model, entity_id)

    def list(self, offset: int = 0, limit: int = 100) -> list[ModelT]:
        return list(self.session.query(self.model).offset(offset).limit(limit).all())

    def create(self, data: dict) -> ModelT:
        entity = self.model(**data)
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def update(self, entity_id: str, data: dict) -> ModelT | None:
        entity = self.get(entity_id)
        if entity is None:
            return None
        for key, value in data.items():
            setattr(entity, key, value)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def delete(self, entity_id: str) -> bool:
        entity = self.get(entity_id)
        if entity is None:
            return False
        self.session.delete(entity)
        self.session.commit()
        return True
