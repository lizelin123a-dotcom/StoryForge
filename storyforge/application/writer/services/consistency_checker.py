from storyforge.domain.node.node import ChapterNode

JUMPY_PAIRS = {("憋屈", "爽"), ("焦虑", "满足"), ("紧张", "回味")}


def check_node_consistency(nodes: list[ChapterNode]) -> dict:
    issues: list[str] = []
    if not nodes:
        return {"passed": False, "issues": ["节点列表为空"]}

    sorted_nodes = sorted(nodes, key=lambda item: item.index)
    for expected_index, node in enumerate(sorted_nodes, start=1):
        if node.index != expected_index:
            issues.append(f"节点序号不连续：期望 {expected_index}，实际 {node.index}")
        if node.content is not None and not node.content.strip():
            issues.append(f"节点 {node.index} content 为空字符串")

    emotions = [node.emotion_purpose for node in sorted_nodes]
    for left, right in zip(emotions, emotions[1:]):
        for bad_left, bad_right in JUMPY_PAIRS:
            if bad_left in left and bad_right in right:
                issues.append(f"情绪跳转过快：{bad_left} 直接跳到 {bad_right}，缺少过渡节点")

    node_types = [node.node_type.lower() for node in sorted_nodes]
    if "pressure" in node_types and "burst" in node_types:
        if node_types.index("burst") < node_types.index("pressure"):
            issues.append("爽点 burst 出现在 pressure 之前，压爆顺序可能不合理")
    if node_types[-1] != "newsetup":
        issues.append("结尾节点不是 newsetup，追读钩子不足")

    return {"passed": not issues, "issues": issues}
