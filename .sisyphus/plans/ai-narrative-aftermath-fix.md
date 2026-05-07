# AI叙事一致性 + 后果反馈个性化 — 实施计划

## TL;DR

> **快速概览**：修复文字冒险游戏的两个致命体验问题——AI叙事与选项脱节、后果反馈千篇一律。核心策略：增强AI Prompt约束 + 关键词语义校验兜底 + AI生成个性化后果叙事替代硬编码模板。
> 
> **交付物**：
> - `ai_service.py` — SYSTEM_PROMPT 增强 + 新增 `generate_aftermath()` 方法
> - `game_service.py` — Prompt约束 + 语义校验兜底 + 后果叙事AI优先
> - `ai_validator.py` — 新增第四层语义一致性验证
> 
> **预估工作量**：Medium (~6小时)
> **并行执行**：YES — 3 waves
> **关键路径**：Wave 1 (foundation) → Wave 2 (integration) → Wave 3 (polish)

---

## Context

### 原始请求
基于 `/Users/haochen/data/note/obsidian_note/opencode/2026-05-07/random_story_ux_deep_analysis_4_6.md` 中的推荐实施路线（Phase 1方案A），立即实施两个致命级AI体验问题的修复。

### 分析摘要

**问题 #4 — AI叙事与选项不匹配（致命）**：
- 根因：AI单次生成叙事+选项时缺乏一致性约束，5层链路（YAML→Prompt→AI生成→校验→后处理）均无语义校验
- 方案：增强 Prompt 约束 + 关键词覆盖校验 + 不匹配时兜底降级到 default_options

**问题 #6 — 事件反馈模板化（致命）**：
- 根因：后果叙事完全绕过AI，由 CONSEQUENCE_TEMPLATES 硬编码模板生成，{action_desc} = "选择了「xxx」"
- 方案：双层系统 — AI生成个性化后果叙事（优先）→ 模板兜底（AI失败时降级）

### 已有代码基础
- `_build_ai_prompt()` 位于 game_service.py:151-203，已在问题 #10 修复中更新（"炼气"等改动）
- `_build_consequence_narrative()` 位于 game_service.py:346-407
- `CONSEQUENCE_TEMPLATES` 位于 game_service.py:321-342
- `validate_schema()` 位于 ai_validator.py:43-63
- `SYSTEM_PROMPT` 位于 ai_service.py:16-92

---

## Work Objectives

### 核心目标
让AI生成的叙事-选项高度一致，让每次选择后的后果叙事个性化、沉浸式。

### 具体交付物
- `app/services/ai_service.py` — SYSTEM_PROMPT增加一致性指令 + aftermath角色 + `generate_aftermath()` 方法
- `app/services/ai_validator.py` — 新增 `check_narrative_option_alignment()` 第四层语义校验
- `app/services/game_service.py` — Prompt约束增强 + 语义校验兜底 + 后果叙事AI优先重构
- `tests/test_services/test_ai_validator.py` — 新增语义校验测试（如不存在则内联到现有测试）

### Definition of Done
- [ ] AI生成的选项中，每条选项至少包含1个叙事中的关键名词（关键词校验通过率 ≥ 80%）
- [ ] 后果叙事不再使用"你选择了「xxx」"模板句式
- [ ] AI后果生成失败时自动降级到优化后的模板
- [ ] `uv run pytest` 全部通过（515+）
- [ ] `vue-tsc --noEmit` 无错误

### Must Have
- 新增 Constraint 不引入额外API调用次数上限（aftermath用deepseek-chat，理论上每次选择多1次调用）
- 模板兜底机制不可移除（AI失败时游戏仍可运行）
- 保持向后兼容（旧版游戏状态、旧版AI输出格式）

### Must NOT Have
- 不修改76个YAML模板（模板重写是Phase 3长期优化）
- 不引入两遍AI生成（方案B，成本翻倍）
- 不修改前端代码（纯后端AI系统修改）
- 不修改 `handle_breakthrough_choice()`（突破后果叙事已独立处理）

---

## Verification Strategy

> **零人工介入** — 所有验证由agent自动执行

### 测试决策
- **基础设施存在**：YES（pytest + vitest）
- **自动化测试**：Tests after（先实施后补测试）
- **框架**：pytest (backend)
- **Agent QA**：每个任务包含 curl/bash 验证场景

### QA策略
- 后端API：通过 curl 调用 `/api/v1/game/event` 和 `/api/v1/game/event/choose` 验证AI输出
- 语义校验：单元测试验证 `check_narrative_option_alignment()` 函数的判断逻辑

---

## Execution Strategy

### 并行执行 Waves

```
Wave 1 (立即开始 — foundation，最大并行):
├── Task 1: SYSTEM_PROMPT增强 + aftermath角色 (ai_service.py)
├── Task 2: Prompt约束增强 (game_service.py:_build_ai_prompt)
├── Task 3: 关键词语义校验函数 (ai_validator.py)
└── Task 4: AI aftermath生成方法 (ai_service.py:generate_aftermath)

Wave 2 (依赖 Wave 1 — integration):
├── Task 5: 语义校验兜底降级 (game_service.py:get_next_event)
├── Task 6: 后果叙事AI优先重构 (game_service.py:_build_consequence_narrative)
└── Task 7: process_choice传参适配 (game_service.py:process_choice)

Wave 3 (依赖 Wave 2 — polish + test):
├── Task 8: 优化CONSEQUENCE_TEMPLATES措辞
└── Task 9: 语义校验单元测试

Wave FINAL (验证):
├── Task F1: 完整pytest + vue-tsc
└── Task F2: 手动QA — curl验证AI输出一致性
```

### 依赖矩阵

- **1,2,3,4**: 无依赖 → Wave 1 全并行
- **5**: 依赖 1,2,3
- **6**: 依赖 4
- **7**: 依赖 6
- **8**: 依赖 6,7
- **9**: 依赖 3

### Agent分配摘要

- **Wave 1**: 4个 `deep` agent 并行
- **Wave 2**: 1个 `deep` agent (Task 5,6,7 融合为一个，因为都修改 game_service.py)
- **Wave 3**: 2个 agent 并行 (Task 8 deep, Task 9 unspecified-high)

---

## TODOs

---

- [x] 1. SYSTEM_PROMPT增强 + aftermath生成角色

  **What to do**:
  - 在 `SYSTEM_PROMPT` 的"选项规则"部分新增叙事-选项一致性约束
  - 新增 aftermath 生成角色说明段落
  - 在上下文变量说明中增加 aftermath 相关字段说明

  **Must NOT do**:
  - 不修改 JSON schema 结构
  - 不改动"炼气"相关已有指令（问题#10已修复）

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: `["karpathy-guidelines"]`

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 1, with Tasks 2,3,4)
  - **Blocks**: Task 5,6

  **References**:
  - `app/services/ai_service.py:16-92` — 当前 SYSTEM_PROMPT 全文
  - `app/services/ai_service.py:62-66` — 现有"选项规则"部分，在此之后追加

  **Acceptance Criteria**:
  - [ ] SYSTEM_PROMPT 中包含"叙事-选项一致性"明确约束
  - [ ] SYSTEM_PROMPT 中包含 aftermath 生成角色说明
  - [ ] bash: `grep -c "叙事-选项一致性" app/services/ai_service.py` → ≥1
  - [ ] bash: `grep -c "aftermath" app/services/ai_service.py` → ≥2

  **QA Scenarios**:
  ```
  Scenario: AI根据增强后的SYSTEM_PROMPT生成一致性输出
    Tool: Bash (curl)
    Preconditions: DEEPSEEK_API_KEY已设置, 后端运行中
    Steps:
      1. 启动后端: uv run uvicorn app.main:app --port 8000 &
      2. 创建游戏: curl -X POST http://localhost:8000/api/v1/game/start -H "Content-Type: application/json" -d '{"name":"测试","gender":"男","talent_card_ids":["talent_001","talent_002","talent_003"],"attributes":{"rootBone":3,"comprehension":3,"mindset":2,"luck":2}}'
      3. 获取事件: curl -X POST http://localhost:8000/api/v1/game/event -H "Content-Type: application/json" -d '{"session_id":"<SESSION_ID>"}'
      4. 验证: 返回的narrative和options存在
    Expected Result: HTTP 200, narrative非空, options数组长度≥1
    Evidence: .sisyphus/evidence/task-1-system-prompt.json
  ```

  **Commit**: YES
  - Message: `feat(ai): 增强SYSTEM_PROMPT叙事一致性约束和aftermath角色`
  - Files: `app/services/ai_service.py`

---

- [x] 2. _build_ai_prompt() 增强选项约束

  **What to do**:
  - 在 `_build_ai_prompt()` 末尾（第201行之后）追加严格的选项约束指令：
    1. "叙事中出现的具体人物、物品、事件必须在选项中体现"
    2. "每个选项必须是叙事中角色的合理行为选择"
    3. "选项文本应使用叙事中的关键名词"
  - 给出正面和反面的具体示例

  **Must NOT do**:
  - 不修改函数签名
  - 不改变已有 prompt 结构

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: `["karpathy-guidelines"]`

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 1, with Tasks 1,3,4)
  - **Blocks**: Task 5

  **References**:
  - `app/services/game_service.py:151-203` — `_build_ai_prompt()` 当前实现
  - `app/services/game_service.py:200-201` — 现有末尾约束（"请基于【事件标题】..."），在此之后追加

  **Acceptance Criteria**:
  - [ ] Prompt 末尾包含"选项约束"或"一致性"关键词
  - [ ] bash: `grep -c "选项约束" app/services/game_service.py` → ≥1

  **QA Scenarios**:
  ```
  Scenario: Prompt构建包含新的选项约束指令
    Tool: Bash (python)
    Preconditions: 后端可导入
    Steps:
      1. python -c "from app.services.game_service import _build_ai_prompt; prompt = _build_ai_prompt({'title':'test','event_type':'daily','prompt':'测试','player':{'realm':'凡人','age':20}}, {'attributes':{'rootBone':3,'comprehension':3,'mindset':2,'luck':2},'faction':''}); assert '选项约束' in prompt or '一致性' in prompt; print('PASS')"
    Expected Result: 输出 "PASS"
    Evidence: .sisyphus/evidence/task-2-prompt-constraint.txt
  ```

  **Commit**: YES
  - Message: `feat(ai): 增强_build_ai_prompt选项约束指令`
  - Files: `app/services/game_service.py`

---

- [x] 3. ai_validator.py 新增语义一致性校验

  **What to do**:
  - 新增 `check_narrative_option_alignment(narrative: str, options: list[dict]) -> bool` 函数
  - 提取叙事中的中文关键词（2字及以上），检查每条选项是否引用至少1个
  - 若任一选项完全无语义关联，返回 False

  **Must NOT do**:
  - 不移除已有的 validate_schema / check_content_safety
  - 不引入第三方NLP库（仅用re正则）

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: `["karpathy-guidelines"]`

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 1, with Tasks 1,2,4)
  - **Blocks**: Task 5,9

  **References**:
  - `app/services/ai_validator.py:43-63` — 现有 validate_schema() 模式，新增函数应遵循相同风格
  - `app/services/ai_validator.py:8-11` — FORBIDDEN_WORDS 模式，关键词可参考

  **Acceptance Criteria**:
  - [ ] `check_narrative_option_alignment("老者看中你的灵草", [{"text":"出售灵草"}])` → True
  - [ ] `check_narrative_option_alignment("老者看中你的灵草", [{"text":"购买丹药"}])` → False
  - [ ] bash: `python -c "from app.services.ai_validator import check_narrative_option_alignment; assert check_narrative_option_alignment('老者看中你的灵草', [{'text':'出售灵草'}]) == True; assert check_narrative_option_alignment('老者看中你的灵草', [{'text':'购买丹药'}]) == False; print('ALL PASS')"`

  **QA Scenarios**:
  ```
  Scenario: 语义一致性校验正确识别匹配/不匹配
    Tool: Bash (python)
    Preconditions: 文件已保存
    Steps:
      1. 导入函数并测试匹配场景
      2. 测试不匹配场景
      3. 测试边界场景（空narrative、空options）
    Expected Result: 所有断言通过
    Evidence: .sisyphus/evidence/task-3-alignment-check.txt
  ```

  **Commit**: YES
  - Message: `feat(ai): 新增check_narrative_option_alignment语义校验`
  - Files: `app/services/ai_validator.py`

---

- [x] 4. ai_service.py 新增 generate_aftermath() 方法

  **What to do**:
  - 在 `DeepSeekService` 类中新增 `generate_aftermath(context: dict) -> dict | None` 方法
  - 构建 aftermath 生成 prompt，包含：事件标题/类型/叙事原文/玩家选择/修为变化/灵石变化/年龄增长/玩家境界
  - 使用 `deepseek-chat` 模型（更快更便宜），`temperature=0.7`, `max_tokens=200`, `response_format={"type": "json_object"}`
  - 返回 `{"narrative": "..."}` 或异常时返回 None

  **Must NOT do**:
  - 不增加新的类或模块
  - 不使用 `deepseek-reasoner`（避免高成本）

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: `["karpathy-guidelines"]`

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 1, with Tasks 1,2,3)
  - **Blocks**: Task 6

  **References**:
  - `app/services/ai_service.py:97-167` — DeepSeekService 类，新增方法应放在 `__init__` 之后
  - `app/services/ai_service.py:138-167` — `generate_event()` 方法，参考其 API 调用模式
  - MockAIService 中也需要对应的 mock 方法

  **Acceptance Criteria**:
  - [ ] `DeepSeekService` 具有 `generate_aftermath` 方法
  - [ ] `MockAIService` 具有对应的 mock 实现（返回固定叙事或None）
  - [ ] bash: `grep -c "def generate_aftermath" app/services/ai_service.py` → ≥2 (DeepSeekService + MockAIService)

  **QA Scenarios**:
  ```
  Scenario: MockAIService.generate_aftermath返回有效结果
    Tool: Bash (python)
    Preconditions: 无API key（使用MockAIService）
    Steps:
      1. python -c "from app.services.ai_service import MockAIService; svc = MockAIService(); result = svc.generate_aftermath({'title':'测试','event_type':'daily','narrative':'测试叙事','chosen_text':'修炼','cultivation_gain':10}); print('MOCK OK' if result and 'narrative' in result else 'MOCK FAIL')"
    Expected Result: 输出 "MOCK OK"
    Evidence: .sisyphus/evidence/task-4-aftermath-mock.txt
  ```

  **Commit**: YES
  - Message: `feat(ai): 新增generate_aftermath方法用于个性化后果叙事生成`
  - Files: `app/services/ai_service.py`

---

- [x] 5. game_service.py 语义校验兜底降级逻辑

  **What to do**:
  - 在 `get_next_event()` 的 AI option 接受逻辑处（约第282行），增加语义校验：
  - AI option 通过 schema 校验后 → 调用 `check_narrative_option_alignment(narrative, cleaned)`
  - 若校验失败 → 使用模板 `default_options` 替代 AI options（保持 narrative 不变）
  - 添加 `logger.warning` 记录降级事件

  **Must NOT do**:
  - 不改变 narrative 的处理逻辑（narrative 仍使用 AI 生成）
  - 不修改 option 的 consequences 处理

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: `["karpathy-guidelines"]`

  **Parallelization**:
  - **Can Run In Parallel**: NO (Wave 2, after Tasks 1,2,3)
  - **Blocks**: Task 8

  **References**:
  - `app/services/game_service.py:258-283` — AI option 接受逻辑，在第282行之前插入校验
  - `app/services/ai_validator.py` — 使用 `from app.services.ai_validator import check_narrative_option_alignment`

  **Acceptance Criteria**:
  - [ ] 当 AI options 与 narrative 不匹配时，使用 default_options
  - [ ] bash: `grep -c "check_narrative_option_alignment" app/services/game_service.py` → ≥1
  - [ ] bash: `grep -c "logger.warning.*options.*narrative" app/services/game_service.py` → ≥1

  **QA Scenarios**:
  ```
  Scenario: 不匹配的AI options被替换为default_options
    Tool: Bash (python)
    Preconditions: 使用MockAIService
    Steps:
      1. 模拟AI返回与narrative不匹配的options
      2. 调用get_next_event()
      3. 验证返回的options是default_options而非AI生成的
    Expected Result: options来自模板而非AI
    Evidence: .sisyphus/evidence/task-5-fallback.txt
  ```

  **Commit**: YES
  - Message: `fix(ai): 增加叙事-选项语义校验不匹配时兜底降级`
  - Files: `app/services/game_service.py`

---

- [x] 6. _build_consequence_narrative() AI优先重构

  **What to do**:
  - 修改 `_build_consequence_narrative()` 函数签名，增加 `ai_service=None` 和 `event_context=None` 可选参数
  - 在函数开头：若 `ai_service` 和 `event_context` 都存在且不是突破事件 → 调用 `ai_service.generate_aftermath()`
  - 若 AI 返回有效叙事文本 → 直接返回
  - 若 AI 返回 None 或异常 → 降级到原有模板逻辑（完全保留现有代码作为 else 分支）
  - 兜底模板逻辑中，改进 `action_desc` 措辞：将 `f"选择了「{chosen_text}」"` 改为更自然的表述

  **Must NOT do**:
  - 不移除 CONSEQUENCE_TEMPLATES（作为兜底保留）
  - 不改变突破后果叙事逻辑（breakthrough_msg路径不受影响）
  - 不改变 narrative_only 路径

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: `["karpathy-guidelines"]`

  **Parallelization**:
  - **Can Run In Parallel**: NO (Wave 2, after Task 4)
  - **Blocks**: Task 7,8

  **References**:
  - `app/services/game_service.py:346-407` — `_build_consequence_narrative()` 当前实现
  - `app/services/game_service.py:321-342` — CONSEQUENCE_TEMPLATES
  - `app/services/game_service.py:402` — `action_desc = f"选择了「{chosen_text}」"` 需改进

  **Acceptance Criteria**:
  - [ ] `_build_consequence_narrative` 签名包含 `ai_service=None, event_context=None`
  - [ ] 当传入 ai_service 时优先调用 AI 生成
  - [ ] 当 AI 失败时降级到模板
  - [ ] bash: `grep -c "generate_aftermath" app/services/game_service.py` → ≥1

  **QA Scenarios**:
  ```
  Scenario: AI后果生成成功时返回个性化叙事
    Tool: Bash (python)
    Preconditions: 使用MockAIService
    Steps:
      1. 创建mock ai_service (generate_aftermath返回 "修炼之后，灵力流转...")
      2. 调用 _build_consequence_narrative(..., ai_service=mock, event_context={...})
      3. 验证返回值是 "修炼之后，灵力流转..." 而非模板文字
    Expected Result: 返回AI生成的叙事文本
    Evidence: .sisyphus/evidence/task-6-ai-aftermath.txt

  Scenario: AI后果生成失败时降级到模板
    Tool: Bash (python)
    Preconditions: MockAIService.generate_aftermath返回None
    Steps:
      1. 创建mock ai_service (generate_aftermath返回None)
      2. 调用 _build_consequence_narrative(..., ai_service=mock, event_context={...})
      3. 验证返回值包含 "修为" 关键词（来自模板）
    Expected Result: 返回模板生成的文本
    Evidence: .sisyphus/evidence/task-6-template-fallback.txt
  ```

  **Commit**: YES
  - Message: `feat(game): 后果叙事AI优先生成，模板兜底降级`
  - Files: `app/services/game_service.py`

---

- [x] 7. process_choice() 传参适配

  **What to do**:
  - 修改 `process_choice()` 中调用 `_build_consequence_narrative()` 的代码（约第563行）
  - 传入 `ai_service=ai_service` 和 `event_context=current_event` 参数
  - 确保 ai_service 实例在 process_choice 上下文中可访问

  **Must NOT do**:
  - 不改变 process_choice 的返回值结构
  - 不修改 aftermath 字段结构

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: `["karpathy-guidelines"]`

  **Parallelization**:
  - **Can Run In Parallel**: NO (Wave 2, after Task 6)
  - **Blocks**: Task 8

  **References**:
  - `app/services/game_service.py:563-568` — 当前后果叙事调用代码
  - `app/services/game_service.py:486-611` — process_choice() 完整实现

  **Acceptance Criteria**:
  - [ ] `_build_consequence_narrative()` 调用传入了 `ai_service` 和 `event_context`
  - [ ] 向后兼容：不传这两个参数时仍可工作

  **QA Scenarios**:
  ```
  Scenario: process_choice正常调用AI后果生成
    Tool: Bash (curl)
    Preconditions: 后端运行中
    Steps:
      1. 启动游戏并获取首个事件
      2. 做出选择: curl -X POST .../event/choose -d '{"session_id":"X","option_id":"opt1"}'
      3. 检查返回的aftermath.narrative是否为自然语言（不含"你选择了"）
    Expected Result: aftermath.narrative 为自然语言描述
    Evidence: .sisyphus/evidence/task-7-aftermath-response.json
  ```

  **Commit**: NO (与 Task 6 合并)
  - Files: `app/services/game_service.py`

---

- [x] 8. 优化 CONSEQUENCE_TEMPLATES 措辞

  **What to do**:
  - 修改 `_build_consequence_narrative()` 兜底模板中的 `action_desc` 生成逻辑：
  - 旧: `action_desc = f"选择了「{chosen_text}」"` 
  - 新: `action_desc = f"你{chosen_text}"` （更自然的融入叙事）
  - 更新 `cultivation_positive` 模板，使 action_desc 前置自然
  - 确保模板中的 `{action_desc}` 占位符与新的填充逻辑兼容

  **Must NOT do**:
  - 不删除任何模板条目
  - 不修改 narrative_only 和 breakthrough 模板

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `["karpathy-guidelines"]`

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 3, with Task 9)
  - **Blocks**: None

  **References**:
  - `app/services/game_service.py:396-407` — action_desc 生成和模板填充逻辑
  - `app/services/game_service.py:321-342` — CONSEQUENCE_TEMPLATES 模板文本

  **Acceptance Criteria**:
  - [ ] 模板输出不再包含 "选择了「" 这个文本片段
  - [ ] bash: `grep -c "选择了「" app/services/game_service.py` → 0

  **QA Scenarios**:
  ```
  Scenario: 兜底模板输出自然语言
    Tool: Bash (python)
    Steps:
      1. 调用 _build_consequence_narrative(chosen_text="修炼功法", cultivation_gain=20, time_span=1, spirit_stones_gain=0)
      2. 验证返回值不包含 "选择了"
      3. 验证返回值包含 "修炼功法" 或 "你修炼功法"
    Expected Result: 自然语言叙事，无元叙述痕迹
    Evidence: .sisyphus/evidence/task-8-template-wording.txt
  ```

  **Commit**: YES
  - Message: `refactor(game): 优化后果叙事模板措辞，去除出戏句式`
  - Files: `app/services/game_service.py`

---

- [x] 9. 语义校验单元测试

  **What to do**:
  - 新增或扩展现有测试文件以覆盖 `check_narrative_option_alignment()` 函数
  - 测试场景：完全匹配、完全不匹配、部分匹配、空输入
  - 若 `test_ai_validator.py` 存在则追加，否则创建

  **Must NOT do**:
  - 不修改已有测试的断言
  - 不引入需要真实AI调用的测试

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: `["karpathy-guidelines"]`

  **Parallelization**:
  - **Can Run In Parallel**: YES (Wave 3, with Task 8)
  - **Blocks**: None

  **References**:
  - `tests/test_services/test_game_service.py` — 参考现有测试结构
  - `app/services/ai_validator.py` — 被测试的函数

  **Acceptance Criteria**:
  - [ ] 至少 4 个测试用例覆盖匹配/不匹配/空输入场景
  - [ ] `uv run pytest tests/ -k "alignment" -q` → all pass

  **QA Scenarios**:
  ```
  Scenario: 测试套件验证语义校验逻辑
    Tool: Bash
    Steps:
      1. uv run pytest tests/ -k "alignment" -v
    Expected Result: 所有新增测试通过
    Evidence: .sisyphus/evidence/task-9-tests.txt
  ```

  **Commit**: YES
  - Message: `test(ai): 新增check_narrative_option_alignment语义校验测试`
  - Files: `tests/test_services/test_ai_validator.py` 或现有文件

---

## Final Verification Wave

> 所有实现任务完成后，运行验证。

- [x] F1. **完整测试套件** — `unspecified-high`
  运行 `uv run pytest -q` 和 `cd web && npx vue-tsc --noEmit`。
  输出: `Pytest [N/N] | Vue-TSC [PASS/FAIL] | VERDICT`

- [x] F2. **AI输出一致性手动QA** — `unspecified-high`
  使用 curl 调用完整游戏流程（start → event → choose → event），检查：
  - AI生成的 narratives 和 options 是否语义一致
  - 后果叙事是否个性化（不含"你选择了"句式）
  - Mock模式验证降级兜底正常工作
  输出: `Consistency [N/5] | Aftermath [N/5] | Fallback [VERIFIED] | VERDICT`

---

## Commit Strategy

- **Wave 1**: 4 commits (每任务独立)
- **Wave 2**: 2 commits (Task 5独立, Task 6+7合并)
- **Wave 3**: 2 commits (Task 8独立, Task 9独立)
- **共**: 8 commits

---

## Success Criteria

### Verification Commands
```bash
# Backend
uv run pytest -q                                    # Expected: 520+ passed
uv run pytest tests/ -k "alignment" -v              # Expected: 新增测试全部通过

# Frontend
cd web && npx vue-tsc --noEmit                      # Expected: no output

# Semantic check
python -c "from app.services.ai_validator import check_narrative_option_alignment; assert check_narrative_option_alignment('老者看中你的灵草', [{'text':'出售灵草'}]) == True; assert check_narrative_option_alignment('老者看中你的灵草', [{'text':'购买丹药'}]) == False; print('OK')"
```

### Final Checklist
- [ ] SYSTEM_PROMPT 包含一致性约束和aftermath角色
- [ ] _build_ai_prompt() 包含选项约束指令
- [ ] check_narrative_option_alignment() 正确判断语义一致性
- [ ] generate_aftermath() 可生成个性化后果叙事
- [ ] 不匹配时兜底降级到 default_options
- [ ] 后果叙事优先使用AI生成
- [ ] 模板措辞不再使用"你选择了"句式
- [ ] 全部测试通过
