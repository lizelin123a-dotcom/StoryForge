from typing import Any


def mark_fallback(payload: dict[str, Any], stage: str, error: Exception | str) -> dict[str, Any]:
    payload["_meta"] = {
        "source": "fallback",
        "stage": stage,
        "reason": str(error),
    }
    return payload


def fallback_notice(payload: Any) -> dict[str, str] | None:
    if isinstance(payload, dict):
        meta = payload.get("_meta")
        if isinstance(meta, dict) and meta.get("source") == "fallback":
            stage = str(meta.get("stage") or "unknown")
            reason = str(meta.get("reason") or "LLM 调用失败")
            return {"stage": stage, "reason": reason}
    return None
