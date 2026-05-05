import os
import shutil
from collections.abc import Iterable
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = PACKAGE_ROOT.parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_DATABASE_PATH = DEFAULT_DATA_DIR / "storyforge.db"
LEGACY_DATABASE_PATHS = (
    PROJECT_ROOT / "storyforge.db",
    PACKAGE_ROOT / "storyforge.db",
)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}")


def _maybe_migrate_legacy_sqlite() -> None:
    if os.getenv("DATABASE_URL") or DEFAULT_DATABASE_PATH.exists():
        return
    for legacy_path in LEGACY_DATABASE_PATHS:
        if legacy_path.exists() and legacy_path.is_file() and legacy_path.stat().st_size > 0:
            DEFAULT_DATA_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy2(legacy_path, DEFAULT_DATABASE_PATH)
            return


_maybe_migrate_legacy_sqlite()


class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_sqlite_novels_table()


def _migrate_sqlite_novels_table() -> None:
    if not DATABASE_URL.startswith("sqlite"):
        return
    inspector = inspect(engine)
    if "novels" not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("novels")}
    migrations: Iterable[tuple[str, str]] = (
        ("world_setting", "ALTER TABLE novels ADD COLUMN world_setting TEXT DEFAULT ''"),
        ("characters", "ALTER TABLE novels ADD COLUMN characters TEXT DEFAULT '[]'"),
        ("target_word_count", "ALTER TABLE novels ADD COLUMN target_word_count INTEGER DEFAULT 120000"),
        ("status", "ALTER TABLE novels ADD COLUMN status VARCHAR DEFAULT 'idle'"),
    )
    with engine.begin() as connection:
        for column_name, statement in migrations:
            if column_name not in existing_columns:
                connection.execute(text(statement))
