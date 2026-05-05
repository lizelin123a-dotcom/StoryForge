from typing import Callable, Any

from storyforge.application.dissect.services.common import extract_json_object
from storyforge.infrastructure.ai.openai_adapter import call_llm

LLMCaller = Callable[[str, str, bool], str]
SHUANG_TYPES = [
    "信息差碾压", "扮猪吃虎", "规则内打脸", "公开处刑", "长辈震惊", "路人助攻", "被瞧不起后爆发", "极限反杀", "宝藏现世", "幕后大佬反应", "打脸后获利", "身份揭露反转", "势力碾压", "资源差距", "双重打脸", "捡漏", "成长对比", "复利积累", "角色等待焦虑",
]
SYSTEM_PROMPT = """你是网文章节爽点分析专家。对照19种核心爽点类型，识别主爽点、辅助爽点、位置、前后情绪、频率。只输出 JSON object。
"""


def analyze_shuang_points(text: str, llm: LLMCaller = call_llm) -> dict[str, Any]:
    prompt = f"""请分析章节爽点。
19种核心爽点类型：{'、'.join(SHUANG_TYPES)}。
输出 JSON：{{"chapter_shuang_points": [{{"position_start": 0, "position_end": 100, "shuang_type": "规则内打脸", "pre_emotion": "憋屈", "post_emotion": "爽"}}], "main_shuang": "主爽点类型", "secondary_shuang": ["辅助爽点"], "frequency": {{"规则内打脸": 1}}}}
章节正文：
{text}
"""
    try:
        data = extract_json_object(llm(prompt, SYSTEM_PROMPT, True))
        data.setdefault("chapter_shuang_points", [])
        data.setdefault("main_shuang", "")
        data.setdefault("secondary_shuang", [])
        data.setdefault("frequency", {})
        return data
    except Exception:
        return _fallback_shuang(text)


def _fallback_shuang(text: str) -> dict[str, Any]:
    keyword_map = {
        "震惊": "长辈震惊",
        "反杀": "极限反杀",
        "打脸": "规则内打脸",
        "身份": "身份揭露反转",
        "宝物": "宝藏现世",
        "嘲笑": "被瞧不起后爆发",
    }
    points = []
    frequency: dict[str, int] = {}
    for keyword, shuang_type in keyword_map.items():
        pos = text.find(keyword)
        if pos >= 0:
            points.append({"position_start": pos, "position_end": pos + len(keyword), "shuang_type": shuang_type, "pre_emotion": "憋屈", "post_emotion": "爽"})
            frequency[shuang_type] = frequency.get(shuang_type, 0) + 1
    main = max(frequency, key=frequency.get) if frequency else ""
    return {"chapter_shuang_points": points, "main_shuang": main, "secondary_shuang": [key for key in frequency if key != main], "frequency": frequency}
