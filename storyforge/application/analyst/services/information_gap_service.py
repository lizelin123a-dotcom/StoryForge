from typing import Any, Callable

from storyforge.application.dissect.services.common import extract_json_object
from storyforge.infrastructure.ai.openai_adapter import call_llm

LLMCaller = Callable[[str, str, bool], str]
SYSTEM_PROMPT = """你是网文信息差分析专家。识别读者知道但角色不知道、角色知道但读者不知道、读者和角色都知道但第三方不知道的信息差。只输出 JSON object。
"""


def analyze_information_gap(text: str, llm: LLMCaller = call_llm) -> dict[str, Any]:
    prompt = f"""请分析章节信息差。
输出 JSON：{{"gaps": [{{"type": "reader_knows/character_knows/third_party", "description": "信息差描述", "quality": "低/中/高"}}], "no_gap_warning": false, "suggestions": ["建议"]}}
正文：
{text}
"""
    try:
        data = extract_json_object(llm(prompt, SYSTEM_PROMPT, True))
        gaps = data.get("gaps", [])
        data["no_gap_warning"] = bool(data.get("no_gap_warning", not gaps))
        data.setdefault("suggestions", [])
        return data
    except Exception:
        return _fallback_gap(text)


def _fallback_gap(text: str) -> dict[str, Any]:
    gaps = []
    if "读者知道" in text or "其实" in text:
        gaps.append({"type": "reader_knows", "description": "文本存在读者提前知道的信息", "quality": "中"})
    if "秘密" in text or "没有人知道" in text:
        gaps.append({"type": "character_knows", "description": "角色可能掌握未公开秘密", "quality": "中"})
    if "众人不知" in text or "他们不知道" in text:
        gaps.append({"type": "third_party", "description": "读者与主角知道而第三方不知道", "quality": "高"})
    return {"gaps": gaps, "no_gap_warning": not gaps, "suggestions": [] if gaps else ["增加读者已知但配角未知的信息，制造期待感"]}
