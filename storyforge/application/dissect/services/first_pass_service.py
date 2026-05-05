import uuid
from typing import Callable

from storyforge.domain.dissect.dissected_chapter import DissectedChapter, ShuangPoint
from storyforge.domain.dissect.source_novel import SourceNovel
from storyforge.infrastructure.ai.openai_adapter import call_llm

from .common import extract_json_object, split_chapters

LLMCaller = Callable[[str, str, bool], str]

SHUANG_TYPES = "、".join([
    "信息差碾压", "扮猪吃虎", "规则内打脸", "公开处刑", "长辈震惊", "路人助攻", "被瞧不起后爆发", "极限反杀", "宝藏现世", "幕后大佬反应", "打脸后获利", "身份揭露反转", "势力碾压", "资源差距", "双重打脸", "捡漏", "成长对比", "复利积累", "角色等待焦虑",
])

SYSTEM_PROMPT = f"""你是网文标书拆解专家，执行三遍拆书法的第一遍阅读模式。
目标：看懂章节结构、标记爽点位置、记录情绪变化、识别核心矛盾。
爽点核心节奏公式：压 → 压 → 安全期（预告） → 压 → 压 → 爆发。
19种核心爽点类型：{SHUANG_TYPES}。
必须只输出 JSON object，不要解释。
"""


def run_first_pass(source_novel: SourceNovel, llm: LLMCaller = call_llm) -> list[DissectedChapter]:
    results: list[DissectedChapter] = []
    for chapter_index, title, content, offset in split_chapters(source_novel.raw_text):
        prompt = f"""请对下面章节做第一遍拆解。
输出 JSON 格式：
{{
  "title": "章节标题",
  "emotional_curve": {{"start": "情绪", "middle": "情绪", "end": "情绪", "notes": ["变化说明"]}},
  "structure_summary": "该章节在整体故事中的位置和功能",
  "core_conflict": "核心矛盾",
  "shuang_points": [
    {{
      "position_start": 0,
      "position_end": 100,
      "shuang_type": "必须是19种核心爽点之一",
      "pre_emotion": "爽点前读者情绪",
      "post_emotion": "爽点后读者情绪",
      "setup_word_count": 800,
      "burst_word_count": 300,
      "info_gap_level": "低/中/高",
      "involved_interests": ["利益1", "利益2"]
    }}
  ]
}}
位置使用章节内字符偏移。没有爽点则 shuang_points 输出空数组。

章节标题：{title}
章节序号：{chapter_index}
章节正文：
{content}
"""
        data = extract_json_object(llm(prompt, SYSTEM_PROMPT, True))
        shuang_points = [ShuangPoint(**item) for item in data.get("shuang_points", [])]
        results.append(
            DissectedChapter(
                id=str(uuid.uuid4()),
                source_novel_id=source_novel.id,
                chapter_index=chapter_index,
                title=str(data.get("title") or title),
                shuang_points=shuang_points,
                emotional_curve=dict(data.get("emotional_curve") or {}),
                structure_summary=str(data.get("structure_summary") or ""),
                core_conflict=str(data.get("core_conflict") or ""),
            )
        )
    return results
