# Learnings — ai-narrative-aftermath-fix

## Conventions & Patterns
- 后端服务在 `app/services/` 下
- 校验逻辑在 `ai_validator.py`，3层：JSON解析 → Schema校验 → 业务规则
- AI服务通过 `DeepSeekService` 和 `MockAIService` 提供
- `_build_ai_prompt()` 在 game_service.py:151-203
- `_build_consequence_narrative()` 在 game_service.py:346-407
- `CONSEQUENCE_TEMPLATES` 在 game_service.py:321-342
- `SYSTEM_PROMPT` 在 ai_service.py:16-92

## Decisions
- 不修改 YAML 模板（Phase 3 长期优化）
- 不引入两遍 AI 生成（方案B，成本翻倍）
- 不修改前端代码（纯后端 AI 系统修改）
- 不修改 handle_breakthrough_choice()（突破后果叙事已独立处理）
- aftermath 使用 deepseek-chat（更快更便宜）
- 模板兜底机制不可移除

## Key Files
- app/services/ai_service.py
- app/services/ai_validator.py
- app/services/game_service.py
- tests/test_services/test_ai_validator.py

## check_narrative_option_alignment() Implementation
- Added to `ai_validator.py` between `check_content_safety()` and `validate_ai_output()`
- **Key insight**: `re.findall(r'[\u4e00-\u9fff]{2,}', text)` is greedy and captures entire Chinese sentences as one match — useless for keyword extraction
- **Solution**: Use sliding window of 2-4 char substrings + `re.fullmatch()` to extract meaningful Chinese keyword fragments
  - Extract all 2/3/4-character Chinese-only substrings as keywords
  - Each option must contain at least one keyword from the narrative
  - Returns `True` for empty inputs (let schema validation handle edge cases)
- Edge cases covered: empty narrative, empty options, options without text key
- Only uses `re` module (no third-party NLP libraries)
- All 21 existing validator tests pass + manual test cases pass

## Semantic Alignment Fallback Integration (2026-05-07)
- Integrated `check_narrative_option_alignment()` into `game_service.py:get_next_event()` line 298
- Import added at line 25: `from app.services.ai_validator import check_narrative_option_alignment`
- Logic: after AI options are cleaned/consequences validated, check alignment before accepting
  - If aligned → use AI options (existing behavior)
  - If not aligned → keep AI narrative, fall back to template `default_options`, log warning
- **MockAIService fix required**: changed default option "下山历练" → "提升修为" to align with the mock's fixed narrative "你在山间修炼，灵气充裕，修为有所增长。" 
  - "下山历练" has zero 2-4 char Chinese substring overlap with the narrative → alignment check fails
  - "提升修为" contains "修为" keyword from narrative → passes
- All 515 tests pass after fix

## _build_consequence_narrative() AI-First Refactor (2026-05-07)
- Signature extended with `ai_service=None, event_context: dict | None = None` (backward compatible)
- AI-first block inserted after `stones_part` calculation, before template selection
- Skip AI path for breakthrough events (`not breakthrough_msg` guard)
- On AI success → return `ai_result["narrative"]` directly, log info
- On AI failure/None → fall through to existing template logic, log warning
- `logger` is NOT at module level in game_service.py (only defined locally in `_handle_cultivation_overflow` at line 517)
  - Fix: added `_logger = logging.getLogger(__name__)` inside the AI-first block
- Call site in `process_choice()` NOT modified — always passes defaults, backward compatible
- CONSEQUENCE_TEMPLATES preserved exactly as-is
- `generate_aftermath` count: 1 in game_service.py ✅
- All 62 game_service tests pass; 509/509 non-e2e tests pass
