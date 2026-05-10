import re
from typing import Any, Callable

from storyforge.application.writer.services.four_questions import answer_four_questions
from storyforge.domain.node.node import ChapterNode, WritingFourQuestions
from storyforge.infrastructure.ai.openai_adapter import call_llm

LLMCaller = Callable[[str, str, bool], str]

SYSTEM_PROMPT = """你是逐节点网文写作引擎，只写现代白话网文正文。

硬规则：
- 只写当前节点，不扩展到节点外。
- 开头三句内必须出现具体冲突、目标或异常，不准只铺氛围。
- 优先写动作、对话、信息露出、冲突逼近、选择、代价、爽点兑现。
- 环境描写最多两句，且必须服务冲突或信息。
- 禁止文艺腔、散文腔、诗化表达、命运感表达、哲理总结、心理分析。
- 禁止段尾升华，禁止漂亮废话，禁止重复段落。
- 字数 200-500 字。
"""

LITERARY_PATTERNS = (
    "暮色", "余晖", "微光", "尘埃", "命运", "宿命", "灵魂", "心底", "心头", "内心深处", "深处",
    "涟漪", "悸动", "破碎", "沉默蔓延", "空气凝固", "世界安静", "心头一震", "眼神复杂",
    "仿佛", "像是", "某种", "难以言说", "说不清", "这一刻", "终于明白", "终于意识到",
    "意识到", "明白了", "这意味着", "这象征", "这标志着", "情绪翻涌", "复杂的情感",
    "命运的齿轮", "无声地", "静静地", "缓缓地", "不由得", "不禁", "忍不住", "下意识",
)
LITERARY_REGEX = (
    r"不是.{1,30}(而是|，是|,是)",
    r"通过.{1,30}(展现|体现|表现)",
    r"他(意识到|明白|感到|感觉到)",
    r"她(意识到|明白|感到|感觉到)",
    r"内心.{0,12}(挣扎|翻涌|震动|复杂)",
    r"空气.{0,8}(凝固|安静|沉默)",
)
IMAGERY_TOKENS = (
    "红烛", "烛火", "火苗", "红绸", "酒面", "杯盏", "珠帘", "金线", "墨痕", "凤纹", "蜡泪", "屏风", "倒烧",
    "微光", "淡金", "无风自动", "泛起", "爬出", "缠上", "映不出", "映出",
)
WEBNOVEL_ACTION_TOKENS = (
    "退婚", "验明", "交代", "让", "请", "滚", "跪", "杀", "拦", "挡", "压", "抢", "夺", "打", "断", "查", "问",
    "开口", "冷笑", "盯", "迈", "按", "递", "收", "撕", "拍", "砸", "跪下", "闭嘴",
)
CONFLICT_TOKENS = ("退婚", "交代", "代价", "规矩", "证据", "当堂", "让她出来", "不配", "羞辱", "反悔", "逼", "局", "演戏")


def generate_node_content(
    node: ChapterNode,
    context: dict[str, Any] | None = None,
    questions: WritingFourQuestions | None = None,
    llm: LLMCaller = call_llm,
) -> ChapterNode:
    four_questions = questions or answer_four_questions(node, context, llm)
    prompt = f"""请按当前节点生成网文正文。

网文节奏硬要求：
- 开头三句内必须让读者知道：谁来了、要做什么、眼前谁/什么在阻拦。
- 不要用一堆异象代替冲突。异象最多一处，而且必须立刻产生后果。
- 每 150 字内至少出现一次：对话、动作、信息变化、压迫、反击、选择之一。
- 如果是退婚/打脸/压迫场，必须把羞辱、规则、阻拦、反击写清楚。
- 环境描写总量不超过全文 20%。
- 禁止连续描写红烛、金线、酒面、珠帘、纹路这类意象。
- 禁止重复段落。

绝对文风要求：
- 写现代白话，不写文艺散文。
- 不要漂亮句子，不要氛围堆砌，不要哲理总结。
- 不写“仿佛、某种、难以言说、命运、灵魂、暮色、余晖、空气凝固、世界安静下来”。
- 不写“他意识到、这意味着、不是X而是Y、通过X展现Y”。
- 愤怒写动作，不写“他很愤怒”；害怕写动作，不写“恐惧蔓延”。

节点约束：
- 只写 node_type={node.node_type} 这一节点，不提前写后续节点。
- 叙事功能 segment_function={node.segment_function or 'action_beat'}，按这个功能组织场面。
- 触发点必须是：{node.trigger_point}
- 情绪目的：{node.emotion_purpose}
- 读者期待：{node.reader_expectation}
- 本节点场景笔记：{node.what_to_write or node.trigger_point}
- 出场角色：{node.characters}
- 微兑现：{node.micro_payoff or '无明确微兑现，但不能空转'}
- 结束画面必须落在：{node.ends_with or '一个具体可感知的画面或状态'}
- 预期字数：{node.expected_word_count}，实际控制在 200-500 字。

写作四问：{four_questions.model_dump()}
上下文：{context or {}}

只输出正文文本，不要标题，不要 JSON，不要解释。
"""
    try:
        content = llm(prompt, SYSTEM_PROMPT, False).strip()
        content = _postprocess_webnovel(content, node=node, llm=llm)
        if getattr(four_questions, "_fallback_reason", ""):
            content += "\n\n（系统提示：写作四问使用了本地写作教学规则。）"
        return node.model_copy(update={"content": content})
    except Exception as exc:
        content = _fallback_node_content(node, four_questions, exc)
        return node.model_copy(update={"content": content})


def _postprocess_webnovel(content: str, *, node: ChapterNode, llm: LLMCaller) -> str:
    content = _dedupe_repeated_blocks(content)
    content = _rewrite_if_literary(content, node=node, llm=llm)
    content = _dedupe_repeated_blocks(content)
    content = _rewrite_if_bad_webnovel_rhythm(content, node=node, llm=llm)
    return _dedupe_repeated_blocks(_light_clean(content))


def literary_risk(text: str) -> dict[str, Any]:
    hits: list[str] = []
    for phrase in LITERARY_PATTERNS:
        if phrase in text:
            hits.append(phrase)
    for pattern in LITERARY_REGEX:
        if re.search(pattern, text):
            hits.append(pattern)
    long_abstract_sentences = re.findall(r"[^。！？\n]{45,}(意识到|意味着|仿佛|某种|内心|情绪|命运)[^。！？\n]*[。！？]", text)
    score = len(hits) * 12 + len(long_abstract_sentences) * 15
    return {"score": min(100, score), "hits": hits[:12]}


def node_quality_report(text: str) -> dict[str, Any]:
    literary = literary_risk(text)
    rhythm = webnovel_rhythm_risk(text)
    score = max(int(literary.get("score") or 0), int(rhythm.get("score") or 0))
    issues = []
    issues.extend(literary.get("hits") or [])
    issues.extend(rhythm.get("reasons") or [])
    return {"score": min(100, score), "passed": score < 30, "issues": issues[:12], "literary": literary, "rhythm": rhythm}


def webnovel_rhythm_risk(text: str) -> dict[str, Any]:
    clean = text.strip()
    paragraphs = [p.strip() for p in re.split(r"\n+", clean) if p.strip()]
    first_part = "".join(paragraphs[:2])[:180]
    imagery_hits = [token for token in IMAGERY_TOKENS if token in clean]
    action_hits = [token for token in WEBNOVEL_ACTION_TOKENS if token in clean]
    conflict_hits = [token for token in CONFLICT_TOKENS if token in clean]
    dialogue_count = len(re.findall(r"“[^”]{1,80}”", clean))
    repeat_count = len(paragraphs) - len(set(paragraphs))
    first_conflict = any(token in first_part for token in (*CONFLICT_TOKENS, *WEBNOVEL_ACTION_TOKENS))
    imagery_overload = len(imagery_hits) >= 5 and len(imagery_hits) > len(action_hits)
    low_dialogue = dialogue_count == 0 and len(clean) > 220
    low_conflict = len(conflict_hits) == 0 and len(clean) > 180
    score = 0
    reasons: list[str] = []
    if not first_conflict:
        score += 25
        reasons.append("开头没有尽快给出冲突/目标/阻碍")
    if imagery_overload:
        score += 30
        reasons.append("意象和氛围过多，动作冲突不足")
    if low_dialogue:
        score += 15
        reasons.append("缺少推动关系或冲突的对话")
    if low_conflict:
        score += 20
        reasons.append("缺少明确冲突词和局面变化")
    if repeat_count:
        score += 35
        reasons.append("存在重复段落")
    return {"score": min(100, score), "reasons": reasons, "imagery_hits": imagery_hits[:10], "action_hits": action_hits[:10], "dialogue_count": dialogue_count, "repeat_count": repeat_count}


def _rewrite_if_literary(content: str, *, node: ChapterNode, llm: LLMCaller) -> str:
    risk = literary_risk(content)
    if int(risk["score"]) < 24:
        return content
    rewrite_prompt = f"""下面这段小说正文有文艺腔、散文腔或心理分析腔。请直接重写成冷静、具体、直接的现代白话网文正文。

必须遵守：
- 保留原剧情信息和节点功能。
- 删除文艺词、抽象心理、哲理总结、段尾升华。
- 把“意识到/感到/仿佛/某种/命运/空气凝固/世界安静”等全部改成动作、对话、现场细节。
- 开头三句内写清目标、阻碍或异常后果。
- 不要解释为什么，不要输出修改说明，只输出重写后的正文。
- 结尾仍落在这个画面：{node.ends_with or '具体可感知的画面或状态'}

命中的风险词：{risk['hits']}

原文：
{content}
"""
    try:
        rewritten = llm(rewrite_prompt, "你是冷硬白话网文改稿编辑，只输出改后正文。", False).strip()
        if int(literary_risk(rewritten)["score"]) <= int(risk["score"]):
            return _light_clean(rewritten)
    except Exception:
        pass
    return _light_clean(content)


def _rewrite_if_bad_webnovel_rhythm(content: str, *, node: ChapterNode, llm: LLMCaller) -> str:
    risk = webnovel_rhythm_risk(content)
    if int(risk["score"]) < 30:
        return content
    rewrite_prompt = f"""下面这段不像网文节奏，问题是：{risk['reasons']}。
请把它重写成更像男频/玄幻网文的正文。

硬要求：
- 开头三句内写清：主角来干什么、对方怎么拦、这场戏的冲突是什么。
- 环境和异象只保留最有用的一两个，其余删掉。
- 用对话推进局面，不要一直写红烛、金线、酒面、珠帘、纹路。
- 每一段都要推进：压迫、试探、反击、揭底、逼对方现身。
- 主角要有明确动作和选择，不能只站着看异象。
- 如果是退婚场，必须写出当堂交锋、对方施压、主角不接招或反压一手。
- 删除重复段落。
- 不要解释修改过程，只输出正文。
- 结尾仍落在：{node.ends_with or '一个明确钩子'}

原文：
{content}
"""
    try:
        rewritten = llm(rewrite_prompt, "你是男频网文节奏改稿编辑。只输出改后正文，冲突优先，爽点优先。", False).strip()
        if int(webnovel_rhythm_risk(rewritten)["score"]) <= int(risk["score"]):
            return rewritten
    except Exception:
        pass
    return content


def _dedupe_repeated_blocks(text: str) -> str:
    paragraphs = [p.strip() for p in re.split(r"\n{1,}", text.strip()) if p.strip()]
    if not paragraphs:
        return text.strip()
    result: list[str] = []
    seen: set[str] = set()
    for paragraph in paragraphs:
        key = re.sub(r"\s+", "", paragraph)
        if len(key) > 4 and key in seen:
            continue
        seen.add(key)
        if len(result) >= 2:
            last_two = "".join(re.sub(r"\s+", "", p) for p in result[-2:])
            current_two = "".join(re.sub(r"\s+", "", p) for p in [paragraph])
            if current_two and current_two in last_two and len(current_two) > 30:
                continue
        result.append(paragraph)
    return "\n".join(result).strip()


def _light_clean(text: str) -> str:
    replacements = {
        "仿佛": "像",
        "某种": "一种",
        "难以言说": "说不清",
        "空气凝固": "没人说话",
        "世界安静下来": "周围没人出声",
        "他意识到": "他看出来",
        "她意识到": "她看出来",
        "这意味着": "这说明",
        "不由得": "",
        "不禁": "",
        "下意识地": "",
        "无声地": "",
        "静静地": "",
        "缓缓地": "",
    }
    cleaned = text
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    cleaned = re.sub(r"不是(.{1,30})而是", r"不是\1，是", cleaned)
    return cleaned.strip()


def _fallback_node_content(node: ChapterNode, questions: WritingFourQuestions, error: Exception) -> str:
    return (
        f"{node.trigger_point}\n"
        f"角色先处理眼前动作。场面围绕“{node.emotion_purpose}”推进。"
        f"读者此刻等的是：{node.reader_expectation}。"
        f"这一节承担“{node.node_type}”功能，先把压力落到具体事件，再把下一步行动钩出来。\n"
        f"系统提示：LLM 节点正文生成失败，已使用本地写作规则。原因：{error}"
    )
