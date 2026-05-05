from __future__ import annotations

from functools import lru_cache
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = PACKAGE_ROOT / "knowledge" / "editor_skills"


@lru_cache(maxsize=1)
def list_editor_skills() -> list[dict[str, str]]:
    if not SKILL_DIR.exists():
        return []
    items: list[dict[str, str]] = []
    for path in sorted(SKILL_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8", errors="ignore").strip()
        if not content:
            continue
        title = _extract_title(content) or path.stem
        items.append({"id": path.stem, "title": title, "description": _extract_description(content), "content": content})
    return items


def get_editor_skills(skill_ids: list[str] | None = None, max_chars: int = 3600) -> list[dict[str, str]]:
    skills = list_editor_skills()
    if skill_ids:
        wanted = set(skill_ids)
        skills = [skill for skill in skills if skill["id"] in wanted]
    selected: list[dict[str, str]] = []
    used = 0
    for skill in skills:
        if used >= max_chars:
            break
        content = skill["content"][: max(500, max_chars - used)]
        selected.append({**skill, "content": content})
        used += len(content)
    return selected


def _extract_title(content: str) -> str:
    for line in content.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return ""


def _extract_description(content: str) -> str:
    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]
    return lines[0][:120] if lines else ""
