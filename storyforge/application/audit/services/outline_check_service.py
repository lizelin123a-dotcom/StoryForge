from storyforge.domain.node.node import ChapterNode


def check_chapter_outline(nodes: list[ChapterNode]) -> dict:
    issues: list[str] = []
    if not 5 <= len(nodes) <= 9:
        issues.append("节点数必须为 5-9 个")
    if nodes:
        if nodes[0].node_type.lower() != "hook":
            issues.append("开篇第一节点类型必须是 Hook")
        if nodes[-1].node_type.lower() != "newsetup":
            issues.append("结尾节点类型必须是 NewSetup")
    else:
        issues.append("章纲节点列表为空")

    if not any(node.node_type.lower() == "burst" for node in nodes):
        issues.append("整章至少需要一个 Burst 爽点节点")

    for node in nodes:
        if not 200 <= node.expected_word_count <= 500:
            issues.append(f"节点 {node.index} 预期字数必须在 200-500 之间")
        if not node.emotion_purpose.strip():
            issues.append(f"节点 {node.index} 缺少情绪目的")
        if not node.trigger_point.strip():
            issues.append(f"节点 {node.index} 缺少触发点")

    return {"passed": not issues, "issues": issues}
