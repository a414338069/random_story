import yaml
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent


def load_system_prompt() -> str:
    with open(_PROMPTS_DIR / "system.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["content"]


def load_user_prompt() -> str:
    with open(_PROMPTS_DIR / "user.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["content"]


def render_user_prompt(context: dict) -> str:
    template = load_user_prompt()
    known_keys = {
        "realm", "age", "cultivation", "faction",
        "spirit_stones", "event_count", "event_template", "recent_events",
    }
    result = template
    for key in known_keys:
        val = context.get(key)
        if val is None:
            if key == "recent_events":
                val = "（首次事件）"
            else:
                val = ""
        result = result.replace("{" + key + "}", str(val))
    return result
