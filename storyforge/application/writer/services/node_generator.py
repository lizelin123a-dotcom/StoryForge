from typing import Any, Callable

from storyforge.application.writer.services.four_questions import answer_four_questions
from storyforge.domain.node.node import ChapterNode, WritingFourQuestions
from storyforge.infrastructure.ai.openai_adapter import call_llm

LLMCaller = Callable[[str, str, bool], str]

SYSTEM_PROMPT = """你是逐节点网文写作引擎。
只写当前节点，不扩展到节点外；信息通过剧情展现，避免平铺直叙；遵循写作四问与节点约束；字数 200-500 字。
"""


def generate_node_content(
    node: ChapterNode,
    context: dict[str, Any] | None = None,
    questions: WritingFourQuestions | None = None,
    llm: LLMCaller = call_llm,
) -> ChapterNode:
    four_questions = questions or answer_four_questions(node, context, llm)
    prompt = f"""请按当前节点生成正文。
强约束：
- 只写 node_type={node.node_type} 这一节点，不提前写后续节点。
- 触发点必须是：{node.trigger_point}
- 情绪目的：{node.emotion_purpose}
- 读者期待：{node.reader_expectation}
- 预期字数：{node.expected_word_count}，实际控制在 200-500 字。
- 信息通过动作、对话、场景细节展现，不要说明文堆设定。
- 如果是 pressure，要压出憋屈和焦虑；如果是 burst，要明确爆发爽点。

写作四问：{four_questions.model_dump()}
上下文：{context or {}}

请直接输出正文文本，不要标题，不要 JSON。
"""
    content = llm(prompt, SYSTEM_PROMPT, False).strip()
    return node.model_copy(update={"content": content})
