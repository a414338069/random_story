"""AI output validator — 3-layer validation + fallback template."""

from __future__ import annotations

import json
import re

FORBIDDEN_WORDS = [
    "手机", "电脑", "微信", "枪", "炮",
    "道侣", "善恶值", "法宝", "锻体", "轮回",
]

_NUMERIC_FIELDS = {
    "cultivation_gain", "spirit_stones_gain", "hp_gain",
    "some_other_numeric", "qi_gain", "exp_gain",
}


def parse_json_response(raw: str) -> dict | None:
    # 1. 直接解析
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        pass

    # 2. 去除 markdown 代码块标记
    stripped = re.sub(r"^```(?:json)?\s*\n?", "", raw.strip())
    stripped = re.sub(r"\n?```\s*$", "", stripped).strip()
    try:
        return json.loads(stripped)
    except (json.JSONDecodeError, TypeError):
        pass

    # 3. 去除首尾空白后解析
    try:
        return json.loads(raw.strip())
    except (json.JSONDecodeError, TypeError):
        pass

    return None


def validate_schema(data: dict) -> tuple[bool, dict]:
    narrative = data.get("narrative")
    if not isinstance(narrative, str) or len(narrative) < 20 or len(narrative) > 500:
        return False, {}

    options = data.get("options")
    if not isinstance(options, list) or len(options) < 2 or len(options) > 3:
        return False, {}

    for opt in options:
        if not isinstance(opt, dict):
            return False, {}
        if not isinstance(opt.get("id"), str) or not isinstance(opt.get("text"), str):
            return False, {}

    cleaned: dict = {"narrative": narrative, "options": []}
    for opt in options:
        cleaned_opt = {"id": opt["id"], "text": opt["text"]}
        cleaned["options"].append(cleaned_opt)

    return True, cleaned


def check_content_safety(data: dict) -> tuple[bool, dict]:
    is_safe = True
    cleaned: dict = {"narrative": data["narrative"], "options": []}

    narrative = data["narrative"]
    for word in FORBIDDEN_WORDS:
        if word in narrative:
            narrative = narrative.replace(word, "***")
            is_safe = False
    cleaned["narrative"] = narrative

    for opt in data["options"]:
        text = opt["text"]
        for word in FORBIDDEN_WORDS:
            if word in text:
                text = text.replace(word, "***")
                is_safe = False
        cleaned["options"].append({"id": opt["id"], "text": text})

    return is_safe, cleaned


def validate_ai_output(
    raw: str,
    fallback_narrative: str,
    default_options: list[dict],
) -> dict:
    fallback = {"narrative": fallback_narrative, "options": default_options}

    parsed = parse_json_response(raw)
    if parsed is None:
        return fallback

    is_valid, cleaned = validate_schema(parsed)
    if not is_valid:
        return fallback

    _, safe_data = check_content_safety(cleaned)
    return safe_data
