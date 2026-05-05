from typing import Any, Callable

from storyforge.application.dissect.services.common import extract_json_object
from storyforge.domain.node.node import ChapterNode, WritingFourQuestions
from storyforge.infrastructure.ai.openai_adapter import call_llm

LLMCaller = Callable[[str, str, bool], str]

SYSTEM_PROMPT = """你是逐节点写作前的写作四问助手。
围绕当前节点回答：情绪、角色状态、读者期待、爽点收尾类型。只输出 JSON object。
"""


def answer_four_questions(
    node: ChapterNode,
    context: dict[str, Any] | None = None,
    llm: LLMCaller = call_llm,
) -> WritingFourQuestions:
    prompt = f"""请根据节点定义和上下文填写写作四问。
输出 JSON：{{"emotion": "想传递什么情绪", "character_state": "角色当前状态", "reader_expectation": "读者期待什么", "shuang_type": "这章准备用哪个爽点收尾"}}
节点：{node.model_dump()}
上下文：{context or {}}
"""
    try:
        return WritingFourQuestions(**extract_json_object(llm(prompt, SYSTEM_PROMPT, True)))
    except Exception as exc:
        fallback = WritingFourQuestions(
            emotion=node.emotion_purpose,
            character_state="处在当前节点触发事件带来的压力或行动状态中",
            reader_expectation=node.reader_expectation,
            shuang_type="规则内打脸" if node.node_type == "burst" else "铺垫后爆发",
        )
        setattr(fallback, "_fallback_reason", str(exc))
        return fallback
