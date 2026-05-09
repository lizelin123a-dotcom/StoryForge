from __future__ import annotations

import re
from typing import Any

from storyforge.domain.node.node import ChapterNode

AI_TASTE_PATTERNS = {
    "上帝视角概述": r"本章(讲述|描写|展示|呈现)|主角经历了|故事发展到",
    "抽象心理总结": r"他意识到|她意识到|内心挣扎|复杂的心理|心理变化|情感升华",
    "分析性结论": r"这表明|这意味着|这标志着|通过.{1,20}展现|体现了",
    "不是而是句式": r"不是.{1,30}(而是|，是|,是)",
    "抽象标签": r"关系递进|冲突升级|情感爆发|人物弧光|命运转折",
}
ABSTRACT_EXPECTATION_PATTERNS = r"后续发展|接下来会怎样|继续阅读|剧情推进|故事发展"
CONCRETE_SCENE_HINTS = r"看|听|说|走|推|抓|递|打|停|门|窗|电话|血|灯|雨|桌|手|眼|声音|脚步"


def check_chapter_outline(outline_or_nodes: dict[str, Any] | list[ChapterNode] | list[dict[str, Any]]) -> dict[str, Any]:
    outline = _normalize_outline_input(outline_or_nodes)
    nodes = [node if isinstance(node, ChapterNode) else ChapterNode(**node) for node in outline.get("nodes", [])]
    issues: list[str] = []
    warnings: list[str] = []
    gate_results: list[dict[str, Any]] = []

    _check_basic_structure(nodes, issues, gate_results)
    _check_enhanced_node_fields(nodes, issues, warnings, gate_results)
    _check_memo(outline.get("memo") or {}, issues, warnings, gate_results)
    _check_emotional_design(outline.get("emotional_design") or {}, nodes, issues, warnings, gate_results)
    _check_ai_taste(outline, nodes, issues, warnings, gate_results)

    passed = not issues
    score = _score(gate_results, issues, warnings)
    return {
        "passed": passed,
        "score": score,
        "issues": issues,
        "warnings": warnings,
        "gate_results": gate_results,
        "summary": "章纲门禁通过，可以进入节点写作。" if passed else "章纲门禁未通过，建议先修复关键问题。",
    }


def _normalize_outline_input(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        nodes = value.get("nodes") or []
        return {**value, "nodes": nodes}
    if isinstance(value, list):
        return {"nodes": [node.model_dump() if isinstance(node, ChapterNode) else node for node in value]}
    return {"nodes": []}


def _check_basic_structure(nodes: list[ChapterNode], issues: list[str], gate_results: list[dict[str, Any]]) -> None:
    local: list[str] = []
    if not 5 <= len(nodes) <= 9:
        local.append("节点数必须为 5-9 个")
    if nodes:
        if nodes[0].node_type.lower() != "hook":
            local.append("开篇第一节点类型必须是 Hook")
        if nodes[-1].node_type.lower() != "newsetup":
            local.append("结尾节点类型必须是 NewSetup")
    else:
        local.append("章纲节点列表为空")

    if not any(node.node_type.lower() == "burst" for node in nodes):
        local.append("整章至少需要一个 Burst 爽点节点")

    for node in nodes:
        if not 200 <= node.expected_word_count <= 500:
            local.append(f"节点 {node.index} 预期字数必须在 200-500 之间")
        if not node.emotion_purpose.strip():
            local.append(f"节点 {node.index} 缺少情绪目的")
        if not node.trigger_point.strip():
            local.append(f"节点 {node.index} 缺少触发点")

    issues.extend(local)
    gate_results.append({"name": "基础结构", "passed": not local, "issues": local})


def _check_enhanced_node_fields(nodes: list[ChapterNode], issues: list[str], warnings: list[str], gate_results: list[dict[str, Any]]) -> None:
    local_issues: list[str] = []
    local_warnings: list[str] = []
    for node in nodes:
        if not node.segment_function.strip():
            local_issues.append(f"节点 {node.index} 缺少 segment_function")
        if not node.what_to_write.strip():
            local_issues.append(f"节点 {node.index} 缺少 what_to_write")
        if not node.ends_with.strip():
            local_issues.append(f"节点 {node.index} 缺少 ends_with 结束画面")
        elif len(node.ends_with) < 8:
            local_warnings.append(f"节点 {node.index} ends_with 过短，可能无法作为下一节点锚点")
        if node.what_to_write and not re.search(CONCRETE_SCENE_HINTS, node.what_to_write):
            local_warnings.append(f"节点 {node.index} what_to_write 缺少具体动作或感官锚点")
    issues.extend(local_issues)
    warnings.extend(local_warnings)
    gate_results.append({"name": "节点叙事字段", "passed": not local_issues, "issues": local_issues, "warnings": local_warnings})


def _check_memo(memo: dict[str, Any], issues: list[str], warnings: list[str], gate_results: list[dict[str, Any]]) -> None:
    local_issues: list[str] = []
    local_warnings: list[str] = []
    for key in ["current_task", "reader_expectation"]:
        if not str(memo.get(key) or "").strip():
            local_issues.append(f"memo.{key} 不能为空")
    if re.search(ABSTRACT_EXPECTATION_PATTERNS, str(memo.get("reader_expectation") or "")):
        local_warnings.append("memo.reader_expectation 偏抽象，建议写清读者具体在等哪个答案或哪次兑现")
    payoff = memo.get("payoff_plan") if isinstance(memo.get("payoff_plan"), dict) else {}
    if not any(payoff.get(key) for key in ["must_resolve", "must_hold", "partial_advance"]):
        local_warnings.append("payoff_plan 为空，本章没有明确伏笔推进/压制/兑现计划")
    if not memo.get("required_changes"):
        local_warnings.append("required_changes 为空，章尾状态变化可能不够明确")
    issues.extend(local_issues)
    warnings.extend(local_warnings)
    gate_results.append({"name": "章节 memo", "passed": not local_issues, "issues": local_issues, "warnings": local_warnings})


def _check_emotional_design(design: dict[str, Any], nodes: list[ChapterNode], issues: list[str], warnings: list[str], gate_results: list[dict[str, Any]]) -> None:
    local_issues: list[str] = []
    local_warnings: list[str] = []
    for key in ["primary_mood", "emotional_hook"]:
        if not str(design.get(key) or "").strip():
            local_issues.append(f"emotional_design.{key} 不能为空")
    progression = design.get("mood_progression") if isinstance(design.get("mood_progression"), list) else []
    if len(progression) < 2:
        local_warnings.append("mood_progression 少于 2 段，情绪走向可能不清晰")
    if not any(node.micro_payoff for node in nodes) and not design.get("micro_payoffs"):
        local_warnings.append("本章未设计 micro_payoff，可能缺少读者的小兑现")
    if nodes and nodes[-1].node_type == "newsetup" and not str(design.get("emotional_hook") or "").strip():
        local_issues.append("newsetup 结尾必须配置 emotional_hook")
    issues.extend(local_issues)
    warnings.extend(local_warnings)
    gate_results.append({"name": "情绪设计", "passed": not local_issues, "issues": local_issues, "warnings": local_warnings})


def _check_ai_taste(outline: dict[str, Any], nodes: list[ChapterNode], issues: list[str], warnings: list[str], gate_results: list[dict[str, Any]]) -> None:
    local_warnings: list[str] = []
    fields: list[tuple[str, str]] = []
    memo = outline.get("memo") if isinstance(outline.get("memo"), dict) else {}
    design = outline.get("emotional_design") if isinstance(outline.get("emotional_design"), dict) else {}
    for key, value in memo.items():
        if isinstance(value, str):
            fields.append((f"memo.{key}", value))
    for key, value in design.items():
        if isinstance(value, str):
            fields.append((f"emotional_design.{key}", value))
    for node in nodes:
        fields.extend([
            (f"node[{node.index}].trigger_point", node.trigger_point),
            (f"node[{node.index}].emotion_purpose", node.emotion_purpose),
            (f"node[{node.index}].reader_expectation", node.reader_expectation),
            (f"node[{node.index}].what_to_write", node.what_to_write),
            (f"node[{node.index}].ends_with", node.ends_with),
        ])
    for field, text in fields:
        for name, pattern in AI_TASTE_PATTERNS.items():
            if re.search(pattern, text):
                local_warnings.append(f"{field} 命中{name}：{_clip(text)}")
    warnings.extend(local_warnings)
    gate_results.append({"name": "AI味自检", "passed": True, "issues": [], "warnings": local_warnings})


def _score(gate_results: list[dict[str, Any]], issues: list[str], warnings: list[str]) -> int:
    score = 100 - len(issues) * 14 - len(warnings) * 5
    failed_gates = sum(1 for gate in gate_results if not gate.get("passed"))
    score -= failed_gates * 8
    return max(0, min(100, score))


def _clip(text: str, limit: int = 48) -> str:
    text = str(text).strip().replace("\n", " ")
    return text if len(text) <= limit else text[:limit] + "..."
