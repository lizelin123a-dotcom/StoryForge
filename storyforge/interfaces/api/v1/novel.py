from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from storyforge.infrastructure.ai.openai_adapter import call_llm
from storyforge.infrastructure.persistence.novel_repository import append_editor_chat_messages, create_novel, delete_novel, get_novel, list_editor_chat_messages, list_node_drafts, list_novels, save_chapter_text, save_node_draft, update_target_word_count, upsert_novel_assets

router = APIRouter(tags=["novel"])
LLM_CONFIG_PATH = Path(__file__).resolve().parents[3] / "llm_config.json"


class CharacterSetting(BaseModel):
    name: str = ""
    role: str = ""
    description: str = ""


class NovelCreateRequest(BaseModel):
    title: str = Field(min_length=1)
    world_setting: str = ""
    characters: list[CharacterSetting] = Field(default_factory=list)
    genre: str = "未分类"
    target_word_count: int = Field(default=120000, ge=1)


class NovelUpdateRequest(BaseModel):
    target_word_count: int | None = Field(default=None, ge=1)


class ChapterSaveRequest(BaseModel):
    chapter_index: int = Field(ge=1)
    content: str = ""
    title: str | None = None


class NodeDraftSaveRequest(BaseModel):
    chapter_index: int = Field(ge=1)
    node_index: int = Field(ge=1)
    node_type: str = ""
    content: str = ""
    locked: bool = False
    source: str = "manual"
    sync_chapter: bool = False
    status: str = ""
    appended_to_chapter: bool = False
    target_words: int = 0


class NovelAssetsSaveRequest(BaseModel):
    assets: dict[str, Any] = Field(default_factory=dict)


class EditorChatMessage(BaseModel):
    role: str
    content: str


class EditorChatAppendRequest(BaseModel):
    messages: list[EditorChatMessage] = Field(default_factory=list)


class GenerateSettingsRequest(BaseModel):
    logline: str = Field(min_length=1, max_length=100)
    api_key: str = ""
    api_base_url: str = ""
    model: str = ""


@router.get("/api/v1/novel/list")
def novel_list() -> dict[str, Any]:
    return {"items": list_novels()}


@router.get("/api/v1/novels")
def novels_list_compat() -> dict[str, Any]:
    return novel_list()


@router.get("/api/v1/novel/{novel_id}")
def novel_detail(novel_id: str) -> dict[str, Any]:
    novel = get_novel(novel_id)
    if novel is None:
        raise HTTPException(status_code=404, detail="novel not found")
    return novel


@router.post("/api/v1/novel/create")
def novel_create(request: NovelCreateRequest) -> dict[str, Any]:
    return _create_from_request(request)


@router.post("/api/v1/novel")
def novel_create_compat(request: NovelCreateRequest) -> dict[str, Any]:
    return _create_from_request(request)


@router.post("/api/v1/novel/{novel_id}/chapter")
def novel_save_chapter(novel_id: str, request: ChapterSaveRequest) -> dict[str, Any]:
    if get_novel(novel_id) is None:
        raise HTTPException(status_code=404, detail="novel not found")
    save_chapter_text(novel_id, request.chapter_index, request.content, request.title)
    return get_novel(novel_id) or {}


@router.get("/api/v1/novel/{novel_id}/nodes")
def novel_nodes(novel_id: str) -> dict[str, Any]:
    if get_novel(novel_id) is None:
        raise HTTPException(status_code=404, detail="novel not found")
    return {"items": list_node_drafts(novel_id)}


@router.post("/api/v1/novel/{novel_id}/node")
def novel_save_node(novel_id: str, request: NodeDraftSaveRequest) -> dict[str, Any]:
    if get_novel(novel_id) is None:
        raise HTTPException(status_code=404, detail="novel not found")
    return save_node_draft(novel_id, request.chapter_index, request.node_index, request.node_type, request.content, request.locked, request.source, request.sync_chapter, request.status, request.appended_to_chapter, request.target_words)


@router.get("/api/v1/novel/{novel_id}/editor-chat")
def novel_editor_chat(novel_id: str) -> dict[str, Any]:
    if get_novel(novel_id) is None:
        raise HTTPException(status_code=404, detail="novel not found")
    return {"items": list_editor_chat_messages(novel_id)}


@router.post("/api/v1/novel/{novel_id}/editor-chat")
def novel_append_editor_chat(novel_id: str, request: EditorChatAppendRequest) -> dict[str, Any]:
    if get_novel(novel_id) is None:
        raise HTTPException(status_code=404, detail="novel not found")
    return {"items": append_editor_chat_messages(novel_id, [item.model_dump() for item in request.messages])}


@router.post("/api/v1/novel/{novel_id}/assets")
def novel_save_assets(novel_id: str, request: NovelAssetsSaveRequest) -> dict[str, Any]:
    if get_novel(novel_id) is None:
        raise HTTPException(status_code=404, detail="novel not found")
    return {"assets": upsert_novel_assets(novel_id, request.assets)}


@router.patch("/api/v1/novel/{novel_id}")
def novel_update(novel_id: str, request: NovelUpdateRequest) -> dict[str, Any]:
    novel = update_target_word_count(novel_id, request.target_word_count)
    if novel is None:
        raise HTTPException(status_code=404, detail="novel not found")
    return novel


@router.delete("/api/v1/novel/{novel_id}")
def novel_delete(novel_id: str) -> dict[str, str]:
    if not delete_novel(novel_id):
        raise HTTPException(status_code=404, detail="novel not found")
    return {"status": "deleted"}


@router.post("/api/v1/novel/generate-settings")
def generate_settings(request: GenerateSettingsRequest) -> dict[str, Any]:
    config = _merge_llm_config(request)
    prompt = f"""你是一个小说创作助手。根据用户的一句话灵感，生成一部小说的完整设定。

用户灵感：{request.logline}

请返回 JSON 格式：
{{
  "title": "作品名称",
  "world_setting": "世界观设定，200字以内",
  "characters": [
    {{"name": "角色名", "role": "主角/配角/反派", "description": "角色描述100字以内"}}
  ],
  "genre": "类型",
  "target_word_count": 120000
}}

注意：title 要吸引人；world_setting 要有画面感；characters 至少 3 个角色（主角、配角、反派）。"""
    try:
        content = call_llm(
            prompt=prompt,
            system_prompt="你是一个专业的小说设定生成助手，只返回 JSON。",
            json_mode=True,
            api_key=config["api_key"] or None,
            base_url=config["api_base_url"] or None,
            model=config["active_model"] or None,
        )
        data = json.loads(content)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"generate settings failed: {exc}") from exc
    return _normalize_generated_settings(data)


def _create_from_request(request: NovelCreateRequest) -> dict[str, Any]:
    return create_novel(
        title=request.title,
        world_setting=request.world_setting,
        characters=[item.model_dump() for item in request.characters],
        genre=request.genre,
        target_word_count=request.target_word_count,
    )


def _normalize_generated_settings(data: dict[str, Any]) -> dict[str, Any]:
    characters = data.get("characters") if isinstance(data.get("characters"), list) else []
    normalized_characters = []
    for item in characters:
        if not isinstance(item, dict):
            continue
        normalized_characters.append(
            {
                "name": str(item.get("name") or "未命名角色"),
                "role": str(item.get("role") or "配角"),
                "description": str(item.get("description") or ""),
            }
        )
    return {
        "title": str(data.get("title") or "未命名作品"),
        "world_setting": str(data.get("world_setting") or ""),
        "characters": normalized_characters[:8],
        "genre": str(data.get("genre") or "未分类"),
        "target_word_count": int(data.get("target_word_count") or 120000),
    }


def _default_llm_config() -> dict[str, Any]:
    return {
        "provider_alias": "DeepSeek",
        "api_base_url": "https://api.deepseek.com/v1",
        "api_key": "",
        "models": ["deepseek-chat"],
        "active_model": "deepseek-chat",
    }


def _load_llm_config() -> dict[str, Any]:
    if not LLM_CONFIG_PATH.exists():
        return _default_llm_config()
    try:
        raw = json.loads(LLM_CONFIG_PATH.read_text(encoding="utf-8"))
        default = _default_llm_config()
        active = str(raw.get("active_model") or raw.get("model") or default["active_model"])
        return {
            "provider_alias": str(raw.get("provider_alias") or default["provider_alias"]),
            "api_base_url": str(raw.get("api_base_url") or default["api_base_url"]).rstrip("/"),
            "api_key": str(raw.get("api_key") or ""),
            "models": raw.get("models") if isinstance(raw.get("models"), list) else [active],
            "active_model": active,
        }
    except Exception:
        return _default_llm_config()


def _merge_llm_config(request: GenerateSettingsRequest) -> dict[str, Any]:
    config = _load_llm_config()
    return {
        "api_key": request.api_key or config["api_key"],
        "api_base_url": (request.api_base_url or config["api_base_url"]).rstrip("/"),
        "active_model": request.model or config["active_model"],
    }
