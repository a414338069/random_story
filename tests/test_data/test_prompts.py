from app.data.prompts.loader import load_system_prompt, load_user_prompt, render_user_prompt


class TestSystemPrompt:
    def test_load_system_prompt(self):
        prompt = load_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "修仙" in prompt

    def test_blacklist_not_in_whitelist(self):
        prompt = load_system_prompt()
        allow_start = prompt.find("允许的概念")
        forbid_start = prompt.find("禁止提及的概念")
        assert allow_start > 0
        assert forbid_start > 0
        whitelist_section = prompt[allow_start:forbid_start]
        blacklist = ["道侣", "善恶值", "法宝", "锻体", "轮回", "心魔劫", "赛季", "充值"]
        for word in blacklist:
            assert word not in whitelist_section, f"Blacklist word '{word}' found in whitelist section"

    def test_prompt_length_reasonable(self):
        prompt = load_system_prompt()
        assert len(prompt) < 2000, f"System prompt too long: {len(prompt)} chars"


class TestUserPrompt:
    def test_load_user_prompt(self):
        prompt = load_user_prompt()
        assert isinstance(prompt, str)
        assert "{realm}" in prompt
        assert "{age}" in prompt
        assert "{cultivation}" in prompt

    def test_render_user_prompt_basic(self):
        result = render_user_prompt({
            "realm": "筑基",
            "age": 50,
            "cultivation": 200.0,
            "faction": "逍遥派",
            "spirit_stones": 100,
            "event_count": 10,
            "event_template": "你发现了一处灵脉...",
            "recent_events": "修炼了一整天",
        })
        assert "筑基" in result
        assert "50" in result
        assert "逍遥派" in result
        assert "{realm}" not in result
        assert "{age}" not in result

    def test_render_user_prompt_missing_fields(self):
        result = render_user_prompt({"realm": "凡人", "age": 10})
        assert "凡人" in result
        assert "（首次事件）" in result
        assert "{realm}" not in result
