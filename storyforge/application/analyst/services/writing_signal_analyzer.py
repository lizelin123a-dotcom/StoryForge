from __future__ import annotations

import re
from typing import Any

from storyforge.infrastructure.knowledge import select_writing_guidance

SIGNAL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "情绪": ("怕", "怒", "恨", "疼", "冷", "笑", "哭", "慌", "爽", "羞", "惊", "悔", "压抑", "兴奋", "期待"),
    "钩子": ("突然", "没想到", "谁知", "秘密", "真相", "信", "门", "声音", "发现", "如果", "为什么"),
    "矛盾": ("必须", "却", "但是", "阻止", "威胁", "代价", "选择", "不能", "偏偏", "冲突", "敌人"),
    "爽点": ("赢", "反击", "碾压", "打脸", "突破", "奖励", "震惊", "跪", "臣服", "掌声", "第一"),
    "信息差": ("以为", "其实", "不知道", "隐瞒", "误会", "身份", "底牌", "真相", "秘密", "暴露"),
    "代入感": ("看见", "听见", "闻到", "触到", "疼", "汗", "光", "风", "雨", "血", "手", "眼"),
    "角色行动": ("走", "冲", "抓", "推", "砸", "拔", "写", "说", "盯", "按", "挡", "逃", "追"),
}


def analyze_writing_signals(text: str) -> dict[str, Any]:
    clean = text.strip()
    if not clean:
        return {"signals": [], "summary": "暂无文本可检测。", "suggestions": ["先写下一个段落，检测器会按教学知识库识别情绪、钩子、矛盾、爽点等信号。"], "guidance": []}

    signals = []
    for name, keywords in SIGNAL_KEYWORDS.items():
        hits = [keyword for keyword in keywords if keyword in clean]
        score = min(100, len(hits) * 18 + _pattern_bonus(name, clean))
        signals.append({"name": name, "score": score, "hits": hits[:8], "status": _status(score)})

    weak = [item["name"] for item in signals if int(item["score"]) < 35]
    strong = [item["name"] for item in signals if int(item["score"]) >= 65]
    suggestions = _build_suggestions(weak, strong, clean)
    guidance = select_writing_guidance(*(weak[:2] or ["期待感", "爽点"]), limit=2, max_chars=900)
    return {
        "signals": signals,
        "summary": _summary(signals, clean),
        "suggestions": suggestions,
        "guidance": guidance,
        "word_count": len(clean),
    }


def _pattern_bonus(name: str, text: str) -> int:
    if name == "矛盾" and re.search(r"必须.+?却|想.+?但是|要.+?不能", text):
        return 24
    if name == "信息差" and re.search(r"以为.+?其实|不知道.+?真相|身份.+?暴露", text):
        return 24
    if name == "钩子" and text.rstrip().endswith(("？", "?", "……")):
        return 18
    if name == "代入感" and len(re.findall(r"[，。；、]", text)) >= 4:
        return 8
    return 0


def _status(score: int) -> str:
    if score >= 65:
        return "明显"
    if score >= 35:
        return "存在"
    return "偏弱"


def _summary(signals: list[dict[str, Any]], text: str) -> str:
    strong = [item["name"] for item in signals if int(item["score"]) >= 65]
    weak = [item["name"] for item in signals if int(item["score"]) < 35]
    if strong:
        return f"当前段落较明显的写作信号：{'、'.join(strong)}。"
    return f"当前段落还偏叙述/说明，建议优先补强：{'、'.join(weak[:3])}。"


def _build_suggestions(weak: list[str], strong: list[str], text: str) -> list[str]:
    suggestions: list[str] = []
    if "角色行动" in weak:
        suggestions.append("给角色一个立刻可见的动作，让段落从说明变成事件。")
    if "矛盾" in weak:
        suggestions.append("补一个阻碍或代价：主角想要什么，眼前谁/什么不让他得到。")
    if "钩子" in weak:
        suggestions.append("段尾留一个未解问题、异常细节或新目标，制造下一段期待。")
    if "爽点" in weak and ("矛盾" not in weak):
        suggestions.append("如果本段承担爆发功能，可以加入反击、揭示底牌或局势反转。")
    if "代入感" in weak:
        suggestions.append("增加一个感官细节，例如光线、声音、触感、疼痛或空间压迫。")
    if not suggestions:
        suggestions.append("信号较完整，下一步可检查节奏：铺垫是否过长，爆发是否足够具体。")
    return suggestions[:4]
