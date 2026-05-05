from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from zipfile import ZipFile


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
EMBEDDED_KNOWLEDGE_DIR = PACKAGE_ROOT / "knowledge" / "writing"

KEYWORD_GROUPS: dict[str, tuple[str, ...]] = {
    "开篇": ("开篇", "开头", "第一章"),
    "期待感": ("期待", "钩子", "悬念"),
    "爽点": ("爽点", "打脸", "信息差", "情绪缺口"),
    "结构": ("结构", "章纲", "大纲", "细纲", "单元", "节奏"),
    "角色": ("角色", "人设", "人物"),
    "冲突": ("冲突", "矛盾", "困境", "阻碍"),
    "行文": ("行文", "画面", "代入感", "共情", "打斗"),
}


@lru_cache(maxsize=1)
def load_writing_knowledge() -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    if not EMBEDDED_KNOWLEDGE_DIR.exists():
        return entries
    for path in sorted(EMBEDDED_KNOWLEDGE_DIR.rglob("*.docx")):
        text = _read_docx_text(path)
        if not text:
            continue
        entries.append({
            "title": path.stem,
            "category": path.parent.name,
            "path": str(path.relative_to(PACKAGE_ROOT)),
            "content": text[:3000],
        })
    return entries


def select_writing_guidance(*keywords: str, limit: int = 5, max_chars: int = 4200) -> list[dict[str, str]]:
    entries = load_writing_knowledge()
    if not entries:
        return []
    normalized_keywords = _expand_keywords(keywords)
    scored: list[tuple[int, dict[str, str]]] = []
    for entry in entries:
        haystack = f"{entry['title']}\n{entry['content']}"
        score = sum(haystack.count(keyword) * 3 for keyword in normalized_keywords if keyword)
        score += sum(5 for keyword in normalized_keywords if keyword and keyword in entry["title"])
        if score > 0:
            scored.append((score, entry))
    if not scored:
        scored = [(1, entry) for entry in entries[:limit]]
    selected: list[dict[str, str]] = []
    used_chars = 0
    for _score, entry in sorted(scored, key=lambda item: item[0], reverse=True):
        if len(selected) >= limit or used_chars >= max_chars:
            break
        excerpt = _excerpt(entry["content"], normalized_keywords, max_chars=max(500, (max_chars - used_chars) // max(1, limit - len(selected))))
        selected.append({"title": entry["title"], "category": entry.get("category", ""), "path": entry["path"], "content": excerpt})
        used_chars += len(excerpt)
    return selected


def _read_docx_text(path: Path) -> str:
    try:
        with ZipFile(path) as archive:
            xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    except Exception:
        return ""
    text = re.sub(r"<w:tab\b[^>]*/>", "\t", xml)
    text = re.sub(r"</w:p>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = (
        text.replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&amp;", "&")
        .replace("&quot;", '"')
        .replace("&apos;", "'")
    )
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _expand_keywords(keywords: tuple[str, ...]) -> list[str]:
    expanded: list[str] = []
    for keyword in keywords:
        if not keyword:
            continue
        expanded.append(keyword)
        expanded.extend(KEYWORD_GROUPS.get(keyword, ()))
    return list(dict.fromkeys(expanded))


def _excerpt(text: str, keywords: list[str], max_chars: int) -> str:
    positions = [text.find(keyword) for keyword in keywords if keyword and text.find(keyword) >= 0]
    if not positions:
        return text[:max_chars]
    start = max(0, min(positions) - 220)
    return text[start:start + max_chars]
