from datetime import datetime
from typing import Any

from storyforge.infrastructure.persistence.database import SessionLocal, init_db
from storyforge.infrastructure.persistence.models.daemon import DaemonStateModel


def save_daemon_state(state: dict[str, Any]) -> None:
    init_db()
    novel_id = str(state["novel_id"])
    with SessionLocal() as session:
        existing = session.get(DaemonStateModel, novel_id)
        if existing is None:
            existing = DaemonStateModel(
                novel_id=novel_id,
                status=str(state.get("status", "idle")),
                current_phase=str(state.get("current_phase", "idle")),
                state=state,
                updated_at=datetime.utcnow(),
            )
            session.add(existing)
        else:
            existing.status = str(state.get("status", "idle"))
            existing.current_phase = str(state.get("current_phase", "idle"))
            existing.state = state
            existing.updated_at = datetime.utcnow()
        session.commit()


def load_daemon_state(novel_id: str) -> dict[str, Any] | None:
    init_db()
    with SessionLocal() as session:
        existing = session.get(DaemonStateModel, novel_id)
        if existing is None:
            return None
        return dict(existing.state)


def load_latest_daemon_state() -> dict[str, Any] | None:
    init_db()
    with SessionLocal() as session:
        existing = session.query(DaemonStateModel).order_by(DaemonStateModel.updated_at.desc()).first()
        if existing is None:
            return None
        return dict(existing.state)
