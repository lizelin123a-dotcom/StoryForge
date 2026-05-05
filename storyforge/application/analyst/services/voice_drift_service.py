import re
from statistics import mean


def detect_voice_drift(current_text: str, baseline_texts: list[str]) -> dict:
    baseline_chapters = len(baseline_texts)
    if not baseline_texts:
        return {"similarity_score": 100.0, "drift_detected": False, "drift_detail": "无基准章节，默认不漂移", "baseline_chapters": 0}

    current_features = _features(current_text)
    baseline_features = _average_features(baseline_texts)
    sentence_delta = abs(current_features["avg_sentence_len"] - baseline_features["avg_sentence_len"])
    paragraph_delta = abs(current_features["paragraph_density"] - baseline_features["paragraph_density"])
    dialogue_delta = abs(current_features["dialogue_ratio"] - baseline_features["dialogue_ratio"])
    penalty = min(sentence_delta * 1.2 + paragraph_delta * 20 + dialogue_delta * 35, 100)
    score = round(max(0.0, 100.0 - penalty), 2)
    drift = score < 70
    detail = f"平均句长差 {sentence_delta:.2f}，段落密度差 {paragraph_delta:.2f}，对话比例差 {dialogue_delta:.2f}"
    return {"similarity_score": score, "drift_detected": drift, "drift_detail": detail, "baseline_chapters": baseline_chapters}


def _features(text: str) -> dict[str, float]:
    sentences = [item for item in re.split(r"[。！？!?]", text) if item.strip()]
    paragraphs = [item for item in text.splitlines() if item.strip()]
    dialogue_marks = text.count("“") + text.count("\"")
    length = max(len(text), 1)
    return {
        "avg_sentence_len": mean([len(item) for item in sentences]) if sentences else float(length),
        "paragraph_density": len(paragraphs) / length * 100,
        "dialogue_ratio": dialogue_marks / length,
    }


def _average_features(texts: list[str]) -> dict[str, float]:
    values = [_features(text) for text in texts]
    return {key: mean([item[key] for item in values]) for key in values[0]}
