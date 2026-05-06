# 修仙人生模拟器 — 结构性问题修复

## TL;DR

> **Quick Summary**: 修复三个致命结构性设计缺陷（后果一闪而过、突破自动触发无选择、幼童突破不合理）+ 强烈建议项（突破仪式感、童年叙事丰富化、少年期过渡事件），通过引入生命阶段系统为锚点一次性解决。
> 
> **Deliverables**:
> - 生命阶段系统（后端年龄门控 + 前端阶段展示）
> - 突破独立特殊事件（含丹药选择、仪式感特效）
> - 后果叙事持久化 + 用户主动推进
> - 童年/少年期专属叙事事件
> - 全部通过 TDD 测试覆盖
> 
> **Estimated Effort**: Large（前后端 8+ 文件核心改动 + 10+ 新YAML事件）
> **Parallel Execution**: YES - 4 waves
> **Critical Path**: T0(提交) → T1(生命阶段后端) → T4(突破独立事件后端) → T7(后果持久化前端) → T10(突破仪式感) → F1-F4

---

## Context

### Original Request
用户在游玩后发现三个无法通过简单修复解决的设计层面结构性缺陷，邀请专业评审产出诊断文档。要求基于该方案做详细修复改造计划。

### Interview Summary
**Key Discussions**:
- 范围确认: 用户选择包含「必须修改」+「强烈建议」项
- 测试策略: TDD — 每个任务先写失败测试再实现
- Git 策略: 先提交 T1-T9 Round 3 改动，保持干净基线
- 突破丹药: 沿用现有 `use_pill` 参数机制，不需要额外丹药获取系统

**Research Findings**:
- `event_engine.py` L88 年龄过滤代码已存在，只差数据修改 → 改动成本极低
- `realms.yaml` 凡人~筑基 time_span=1 → 早期年龄增长合理，问题在事件过滤
- 前端 `ChooseResponse.aftermath` 已含 narrative+breakthrough → 后端返回了但前端类型不完整
- `_breakthrough_msg` 只存 state 不存 DB → 清除即可，不需 DB 迁移

### Self-Identified Guardrails (替代 Metis)
- **不引入新数据库表**: 生命阶段由年龄动态计算，不持久化
- **不引入新 API 端点**: 突破事件走现有 `/event` + `/event/choose` 流程
- **保持 AI 叙事不变**: 突破事件由后端构造不走 AI，减少 API 开销
- **保持向后兼容**: 现有 54 个测试必须继续通过（可修改断言适配新行为）
- **YAML 事件数量控制**: 新增事件不超过 15 个，避免过度膨胀

---

## Work Objectives

### Core Objective
引入生命阶段系统为锚点，将突破机制改为独立交互事件，修复后果叙事的持久化和展示问题，使游戏核心循环（选择→后果→突破→成长）形成完整反馈闭环。

### Concrete Deliverables
- `app/services/life_stage.py` — 新增生命阶段计算模块
- `app/services/game_service.py` — 修改溢出处理、事件获取、选择处理
- `app/services/breakthrough.py` — 新增 `build_breakthrough_event()` + 年龄检查
- `app/services/event_engine.py` — 生命阶段过滤增强
- `app/data/events/` — 8个YAML min_age修改 + ~12个新童年/少年事件
- `app/models/event.py` — 突破事件模型扩展
- `web/src/core/types.ts` — EventLogEntry + LoopPhase 扩展
- `web/src/composables/useGameLoop.ts` — 去掉2.5s setTimeout + 突破决策阶段
- `web/src/views/GameMain.vue` — 突破选项UI + 后果展示改进
- `web/src/components/NarrativeLog.vue` — 后果叙事持久化渲染
- `web/src/styles/` — 突破仪式感特效样式

### Definition of Done
- [ ] 3岁幼儿不再触发修炼事件或突破
- [ ] 突破事件是独立特殊事件，含"服丹/直接突破"选项
- [ ] 后果叙事在历史日志中可回看
- [ ] 正常事件后果不再自动推进，需用户点击
- [ ] 54+ 后端测试全通过 + vue-tsc 零错误
- [ ] 浏览器 E2E 验证通过

### Must Have
- 生命阶段门控（age<12 无修炼收益，age<16 突破受限）
- 突破作为独立事件（后端构造，不走AI，含2个选项）
- 后果叙事持久化到 EventLogEntry
- 去掉 2.5s 自动 setTimeout
- 每个任务 TDD（先写测试再实现）

### Must NOT Have (Guardrails)
- **不引入新数据库表/迁移** — 生命阶段由年龄动态计算
- **不引入新 API 端点** — 突破走现有 /event + /event/choose
- **不让 AI 生成突破叙事** — 后端模板构造，确定性强
- **不修改 realms.yaml 境界定义** — time_span 保持不变
- **不修改安静年机制** — 25% 触发率不变
- **不过度抽象** — 生命阶段用简单的 age 区间判断，不搞配置化
- **不超过 15 个新 YAML 事件** — 控制内容膨胀
- **不添加音效** — 仅视觉特效（音效可后续加）

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: YES (pytest 54个 + Vitest)
- **Automated tests**: TDD — 每个任务先写失败测试
- **Framework**: pytest (后端) / Vitest (前端)
- **TDD Flow**: RED (失败测试) → GREEN (最小实现) → REFACTOR

### QA Policy
每个任务包含 agent-executed QA 场景。
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`

- **后端 API**: Bash (curl) — 发请求，断言状态码+字段
- **前端 UI**: Playwright — 导航，交互，断言 DOM，截图
- **数据校验**: Bash (uv run python -m app.data.validate_data)

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 0 (Pre-work — 基线提交):
└── Task 0: 提交 T1-T9 Round 3 改动 [quick]

Wave 1 (Foundation — 后端生命阶段 + 数据):
├── Task 1: 生命阶段后端模块 + 修炼门控 [deep]
├── Task 2: 事件引擎年龄过滤 + 权重调整 [unspecified-high]
├── Task 3: 8个YAML事件 min_age 修改 [quick]
├── Task 4: 突破独立事件 — 后端 [deep]
├── Task 5: 新增童年/少年期叙事事件YAML [unspecified-high]
└── Task 6: 后端 types/models 扩展 [quick]

Wave 2 (Frontend — 游戏循环 + UI):
├── Task 7: 前端类型扩展 + 后果持久化 [unspecified-high]
├── Task 8: useGameLoop 改造 — 去setTimeout + 突破阶段 [deep]
├── Task 9: GameMain.vue 突破选项 + 后果展示 [visual-engineering]
├── Task 10: NarrativeLog 后果叙事渲染 [quick]
└── Task 11: 突破仪式感 CSS 特效 [visual-engineering]

Wave 3 (Integration + Polish):
├── Task 12: 后端测试更新 + 兼容性修复 [unspecified-high]
├── Task 13: 前端测试更新 + E2E [unspecified-high]
└── Task 14: 数据校验 + 文档更新 [quick]

Wave FINAL (4 parallel reviews → user okay):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Real manual QA with Playwright (unspecified-high)
└── Task F4: Scope fidelity check (deep)
→ Present results → Get explicit user okay

Critical Path: T0 → T1 → T4 → T8 → T9 → T12 → F1-F4
Parallel Speedup: ~60% faster than sequential
Max Concurrent: 6 (Wave 1)
```

### Dependency Matrix

| Task | Depends On | Blocks | Wave |
|------|-----------|--------|------|
| T0 | — | T1-T6 | 0 |
| T1 | T0 | T4, T12 | 1 |
| T2 | T0 | T12 | 1 |
| T3 | T0 | T5, T12 | 1 |
| T4 | T1 | T8, T9, T12 | 1 |
| T5 | T3 | T14 | 1 |
| T6 | T0 | T4, T7 | 1 |
| T7 | T6 | T8, T9 | 2 |
| T8 | T4, T7 | T9, T13 | 2 |
| T9 | T8 | T13 | 2 |
| T10 | T7 | T13 | 2 |
| T11 | T9 | — | 2 |
| T12 | T1-T6 | F1-F4 | 3 |
| T13 | T8-T11 | F1-F4 | 3 |
| T14 | T5 | — | 3 |

### Agent Dispatch Summary

- **Wave 0**: 1 — T0 → `quick`
- **Wave 1**: 6 — T1 → `deep`, T2 → `unspecified-high`, T3 → `quick`, T4 → `deep`, T5 → `unspecified-high`, T6 → `quick`
- **Wave 2**: 5 — T7 → `unspecified-high`, T8 → `deep`, T9 → `visual-engineering`, T10 → `quick`, T11 → `visual-engineering`
- **Wave 3**: 3 — T12 → `unspecified-high`, T13 → `unspecified-high`, T14 → `quick`
- **FINAL**: 4 — F1 → `oracle`, F2 → `unspecified-high`, F3 → `unspecified-high`, F4 → `deep`

---

## TODOs

> Implementation + Test = ONE Task. Never separate.
> EVERY task MUST have: Recommended Agent Profile + Parallelization info + QA Scenarios.

- [x] 0. 提交 T1-T9 Round 3 改动

  **What to do**:
  - 检查 `git status` 确认未提交文件列表
  - 使用 `/git-commit-cn` 提交所有 T1-T9 体验修复 + AGENTS.md 知识库生成改动
  - 确认提交后 `git log` 显示新 commit

  **Must NOT do**:
  - 不修改任何代码
  - 不推送远程

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-commit-cn`]
  - **Reason**: 简单 git 操作，需要中文 commit 规范

  **Parallelization**:
  - **Can Run In Parallel**: NO (前置条件)
  - **Parallel Group**: Wave 0
  - **Blocks**: T1-T6
  - **Blocked By**: None

  **References**:
  - `.sisyphus/plans/handoff-round3.md` — 记录了 T1-T9 每项改动内容
  - 项目根目录 `AGENTS.md` — Round 3 新增的知识库文件

  **Acceptance Criteria**:
  - [ ] `git status` 显示 working tree clean
  - [ ] `git log -1 --oneline` 显示新 commit

  **QA Scenarios**:

  ```
  Scenario: 确认 T1-T9 已提交
    Tool: Bash
    Preconditions: 项目根目录
    Steps:
      1. `git status` — 确认无未提交文件
      2. `git log -1 --oneline` — 确认最新 commit 存在
      3. `uv run pytest --co -q` — 确认测试可发现
    Expected Result: working tree clean + 最新 commit 可见
    Evidence: .sisyphus/evidence/task-0-commit-status.txt
  ```

  **Commit**: YES
  - Message: `feat(game): Round 3 T1-T9 体验修复 + AGENTS.md 知识库生成`
  - Files: 全部未提交文件
  - Pre-commit: `uv run pytest`

- [x] 1. 生命阶段后端模块 + 修炼门控

  **What to do**:
  - **新增 `app/services/life_stage.py`**:
    - 定义 `LifeStage` 枚举: `INFANT`(0-3), `CHILD`(4-11), `YOUTH`(12-15), `CULTIVATOR`(16+)
    - `get_life_stage(age: int) -> LifeStage`: 根据年龄返回阶段
    - `get_cultivation_multiplier(age: int) -> float`: INFANT/CHILD=0.0, YOUTH=0.5, CULTIVATOR=1.0
    - `can_attempt_breakthrough(age: int) -> bool`: age >= 16 返回 True
    - `get_breakthrough_penalty(age: int) -> float`: age < 16 时额外 -50% 成功率
  - **修改 `app/services/game_service.py`**:
    - `_calc_cultivation_gain()` L361-372: 乘以 `get_cultivation_multiplier(age)`
    - `process_choice()` L476-480: 若 age < 12 且 consequences 有 cultivation_gain，乘以 multiplier
    - `_handle_cultivation_overflow()` L407-444: 若 `not can_attempt_breakthrough(age)` 则不触发突破，cap cultivation at next_req - 1
    - `_to_engine_context()` L103-111: 新增 `life_stage` 字段
  - **TDD**: 先写测试覆盖所有阶段计算 + 门控逻辑

  **Must NOT do**:
  - 不修改 realms.yaml
  - 不引入新的数据库字段
  - 不修改事件引擎的过滤逻辑（T2 负责）

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: [`test-driven-development`]
  - **Reason**: 核心后端逻辑 + 新模块，需要 TDD 模式

  **Parallelization**:
  - **Can Run In Parallel**: NO (核心基础)
  - **Parallel Group**: Wave 1
  - **Blocks**: T4, T12
  - **Blocked By**: T0

  **References**:
  - `app/services/game_service.py:361-372` — `_calc_cultivation_gain()`: 修炼收益计算，需乘以阶段乘数
  - `app/services/game_service.py:407-444` — `_handle_cultivation_overflow()`: 突破入口，需加年龄检查
  - `app/services/game_service.py:476-480` — `process_choice()` 修炼收益分支
  - `app/services/game_service.py:103-111` — `_to_engine_context()`: 需新增 life_stage
  - `app/services/breakthrough.py:74-126` — `attempt_breakthrough()`: 需加年龄门控（T4 负责）
  - `app/data/realms.yaml` — 凡人 cultivation_req=100, time_span=1（参考，不修改）

  **Acceptance Criteria**:
  - [ ] `app/services/life_stage.py` 文件存在，包含 LifeStage 枚举 + 4个函数
  - [ ] 新测试文件 `tests/test_services/test_life_stage.py` 覆盖全部函数
  - [ ] `uv run pytest tests/test_services/test_life_stage.py` → PASS
  - [ ] age=3 时 cultivation_multiplier=0.0
  - [ ] age=8 时 cultivation_multiplier=0.0
  - [ ] age=14 时 cultivation_multiplier=0.5
  - [ ] age=20 时 cultivation_multiplier=1.0
  - [ ] age=10 时 can_attempt_breakthrough()=False

  **QA Scenarios**:

  ```
  Scenario: 生命阶段计算正确
    Tool: Bash (uv run pytest)
    Preconditions: life_stage.py 已创建
    Steps:
      1. `uv run pytest tests/test_services/test_life_stage.py -v`
      2. 检查全部测试通过
    Expected Result: 所有 life_stage 测试 PASS，覆盖 4 个阶段 + 边界年龄
    Evidence: .sisyphus/evidence/task-1-life-stage-tests.txt

  Scenario: 幼儿不获得修炼收益
    Tool: Bash (curl)
    Preconditions: 后端运行中
    Steps:
      1. 创建新游戏 (POST /api/v1/game/start)
      2. 获取事件 (POST /api/v1/game/event) — 应为叙事事件
      3. 做出选择 (POST /api/v1/game/event/choose)
      4. 检查 aftermath.cultivation_change == 0
    Expected Result: age < 12 时 cultivation_change 为 0
    Evidence: .sisyphus/evidence/task-1-infant-no-cultivation.json

  Scenario: 少年修炼收益减半
    Tool: Bash (curl)
    Preconditions: 后端运行中，模拟 age=14 的状态
    Steps:
      1. 修改测试或使用 mock 设置 age=14
      2. 触发日常事件选择
      3. 检查 cultivation_change <= base_gain * 0.5
    Expected Result: 少年期修炼收益约为正常的一半
    Evidence: .sisyphus/evidence/task-1-youth-half-cultivation.json
  ```

  **Commit**: YES
  - Message: `feat(core): 引入生命阶段系统 + 修炼年龄门控`
  - Files: `app/services/life_stage.py`, `app/services/game_service.py`, `tests/test_services/test_life_stage.py`
  - Pre-commit: `uv run pytest tests/test_services/test_life_stage.py`

- [x] 2. 事件引擎年龄过滤增强

  **What to do**:
  - **修改 `app/services/event_engine.py`**:
    - `filter_templates()` L66-95: 在现有年龄过滤(L88)之后，增加生命阶段过滤逻辑
    - 当 `player_age < 12` 时，仅允许 `narrative_only: true` 的事件通过
    - 当 `player_age` 在 12-15 时，排除 adventure 类型的极端事件
    - 在 `calculate_weights()` L98-124: 为少年期(12-15)事件增加权重因子
  - **TDD**: 先写测试覆盖各年龄段的事件过滤行为

  **Must NOT do**:
  - 不修改 YAML 事件文件（T3 负责）
  - 不修改安静年机制
  - 不修改 fallback 事件

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`test-driven-development`]
  - **Reason**: 中等复杂度的过滤逻辑修改

  **Parallelization**:
  - **Can Run In Parallel**: YES (with T1, T3-T6)
  - **Parallel Group**: Wave 1
  - **Blocks**: T12
  - **Blocked By**: T0

  **References**:
  - `app/services/event_engine.py:66-95` — `filter_templates()`: 核心过滤函数，L88 已有年龄过滤
  - `app/services/event_engine.py:98-124` — `calculate_weights()`: 权重计算，需加年龄因子
  - `app/services/event_engine.py:127-146` — `_build_quiet_year_event()`: 参考其 narrative_only 模式
  - `app/services/event_engine.py:17-38` — `FALLBACK_EVENT`: 全年龄段兜底，保持不变
  - `app/data/events/AGENTS.md` — 64+ YAML 事件模板分类和 schema

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/test_services/test_event_engine.py -v` → 含新增年龄过滤测试且 PASS
  - [ ] age=5 时，`filter_templates()` 只返回 narrative_only 事件
  - [ ] age=14 时，排除 adventure 类型极端事件
  - [ ] age=20 时，全部事件可通过（行为与改前一致）

  **QA Scenarios**:

  ```
  Scenario: 婴幼儿只能触发叙事事件
    Tool: Bash (uv run pytest)
    Steps:
      1. 运行新增测试: `uv run pytest tests/test_services/test_event_engine.py -v -k "age_filter"`
      2. 确认 age=5 时 filter_templates 只返回 narrative_only=True 的模板
    Expected Result: 过滤后模板列表全部 narrative_only=True
    Evidence: .sisyphus/evidence/task-2-age-filter-test.txt

  Scenario: 修仙期无过滤回归
    Tool: Bash (uv run pytest)
    Steps:
      1. 运行测试确认 age=20 时过滤行为不变
    Expected Result: 过滤结果数量与修改前一致
    Evidence: .sisyphus/evidence/task-2-no-regression.txt
  ```

  **Commit**: YES
  - Message: `feat(engine): 事件引擎年龄过滤增强`
  - Files: `app/services/event_engine.py`, `tests/test_services/test_event_engine.py`
  - Pre-commit: `uv run pytest tests/test_services/test_event_engine.py`

- [x] 3. 8个通用事件 min_age 修改

  **What to do**:
  - 修改以下 8 个 YAML 文件的 `trigger_conditions.min_age` 从 `0` 改为 `12`:
    - `app/data/events/daily_010.yaml` (山间采集)
    - `app/data/events/daily_011.yaml` (坊市交易)
    - `app/data/events/daily_012.yaml` (论道切磋)
    - `app/data/events/daily_013.yaml` (秘境探索)
    - `app/data/events/daily_014.yaml` (静坐冥想) — min_age 改为 12
    - `app/data/events/daily_015.yaml` (翻阅古籍)
    - `app/data/events/adventure_007.yaml` (前辈传承)
    - `app/data/events/adventure_008.yaml` (灵脉喷发)

  **Must NOT do**:
  - 不修改 max_age（保持 9999）
  - 不修改事件内容/叙事
  - 不修改其他 YAML 文件

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - **Reason**: 纯数据修改，每个文件改一个数字

  **Parallelization**:
  - **Can Run In Parallel**: YES (with T1, T2, T4-T6)
  - **Parallel Group**: Wave 1
  - **Blocks**: T5, T12
  - **Blocked By**: T0

  **References**:
  - `app/data/events/daily_010.yaml` ~ `daily_015.yaml` — 6个日常事件的 trigger_conditions.min_age: 0
  - `app/data/events/adventure_007.yaml`, `adventure_008.yaml` — 2个冒险事件的 trigger_conditions.min_age: 0
  - 设计评审文档的「缺陷 1」表格 — 列出了全部 8 个事件及合理性分析

  **Acceptance Criteria**:
  - [ ] 8 个文件 `trigger_conditions.min_age` 均为 `12`
  - [ ] `uv run python -m app.data.validate_data` → PASS（YAML 校验通过）
  - [ ] 其余字段不变

  **QA Scenarios**:

  ```
  Scenario: YAML 校验通过
    Tool: Bash
    Steps:
      1. `uv run python -m app.data.validate_data`
      2. 确认无错误
    Expected Result: 全部 YAML 校验通过
    Evidence: .sisyphus/evidence/task-3-yaml-validate.txt

  Scenario: min_age 已更新
    Tool: Bash (grep)
    Steps:
      1. 搜索 8 个文件的 min_age 字段
      2. 确认全部为 12
    Expected Result: daily_010~015 + adventure_007~008 的 min_age 均为 12
    Evidence: .sisyphus/evidence/task-3-min-age-check.txt
  ```

  **Commit**: YES
  - Message: `fix(data): 8个通用事件 min_age 从0改为12`
  - Files: 8 个 YAML 文件
  - Pre-commit: `uv run python -m app.data.validate_data`

- [x] 4. 突破独立事件 — 后端

  **What to do**:
  - **修改 `app/services/game_service.py`**:
    - `_handle_cultivation_overflow()` L407-444: 不再调用 `attempt_breakthrough()`，改为 `state["_pending_breakthrough"] = True`，cap cultivation
    - 新增 `handle_breakthrough_choice(state, use_pill: bool)` 函数: 调用 `attempt_breakthrough(state, use_pill)`，清除 `_pending_breakthrough`，返回突破结果
    - `get_next_event()` L184-269: 开头检查 `state.get("_pending_breakthrough")`，若 True 则返回 `build_breakthrough_event(player_state)` 而非正常 AI 事件
    - 清除 `_breakthrough_msg` 的持久化逻辑（L433/L442），突破结果仅在突破事件中展示
  - **修改 `app/services/breakthrough.py`**:
    - 新增 `build_breakthrough_event(player_state: dict) -> dict`: 返回含两个选项的事件结构（服丹/直接突破）
    - `calculate_success_rate()` L36-48: 增加年龄惩罚（age < 16 时额外 -50%）
    - `attempt_breakthrough()` L74-126: 无需修改签名，use_pill 参数由前端传入
  - **修改 `app/routers/game.py`**:
    - `/event/choose` L109-145: 检测 option_id 为 `use_pill` 或 `direct` 时调用 `handle_breakthrough_choice()` 而非 `process_choice()`
  - **TDD**: 先写测试覆盖突破事件生成 + 选择处理 + 成功/失败路径

  **Must NOT do**:
  - 不新增 API 端点（走现有 /event + /event/choose）
  - 不让 AI 生成突破叙事（后端模板构造）
  - 不修改 realms.yaml
  - 不修改前端（T8-T9 负责）

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: [`test-driven-development`]
  - **Reason**: 核心机制重构，涉及多文件联动，需深度推理

  **Parallelization**:
  - **Can Run In Parallel**: YES (with T2, T3, T5, T6)
  - **Parallel Group**: Wave 1
  - **Blocks**: T8, T9, T12
  - **Blocked By**: T1 (生命阶段模块)

  **References**:
  - `app/services/game_service.py:407-444` — `_handle_cultivation_overflow()`: 当前自动突破入口，需改为 pending 标记
  - `app/services/game_service.py:184-269` — `get_next_event()`: 需在开头检查 pending_breakthrough
  - `app/services/game_service.py:447-566` — `process_choice()`: 参考其状态处理模式
  - `app/services/breakthrough.py:74-126` — `attempt_breakthrough()`: 核心突破逻辑，use_pill 参数已有
  - `app/services/breakthrough.py:36-48` — `calculate_success_rate()`: 需加年龄惩罚
  - `app/routers/game.py:109-145` — `/event/choose` 处理器: 需加突破选项分支
  - `app/models/event.py:57-61` — `BreakthroughInfo`: 参考现有模型
  - 设计评审文档「突破事件模板」— 事件结构的精确 JSON 定义

  **突破事件模板**（后端构造，不走 AI）:
  ```python
  {
      "event_id": "breakthrough_pending",
      "title": "境界突破",
      "narrative": "你的修为已达瓶颈，丹田中灵力如潮水般涌动，周身经脉隐隐作痛。"
                   "一道无形的屏障横亘在前，这是通往下一境界的壁障。",
      "options": [
          {"id": "use_pill", "text": "服用突破丹（成功率 +15%）", "consequences": {}},
          {"id": "direct", "text": "凭自身实力突破", "consequences": {}}
      ],
      "is_breakthrough": true,
      "has_options": True
  }
  ```

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/test_services/test_breakthrough.py -v` → 含独立事件测试且 PASS
  - [ ] `get_next_event()` 在 `_pending_breakthrough=True` 时返回突破事件
  - [ ] 突破事件含 2 个选项: use_pill / direct
  - [ ] `handle_breakthrough_choice(state, use_pill=True)` 成功率比 `use_pill=False` 高
  - [ ] age=10 时 `calculate_success_rate()` 有额外惩罚
  - [ ] 突破结果不再写入 `_breakthrough_msg`

  **QA Scenarios**:

  ```
  Scenario: 修炼溢出触发待突破状态
    Tool: Bash (uv run pytest)
    Steps:
      1. 创建 state cultivation=99, next_req=100
      2. 调用 process_choice 触发 gain=5
      3. 断言 state["_pending_breakthrough"] == True
      4. 断言 cultivation 被限制在 next_req 附近
    Expected Result: pending 标记已设置，cultivation 未溢出
    Evidence: .sisyphus/evidence/task-4-pending-breakthrough.txt

  Scenario: 获取突破事件
    Tool: Bash (uv run pytest)
    Steps:
      1. 设置 state["_pending_breakthrough"] = True
      2. 调用 get_next_event()
      3. 断言返回事件 title="境界突破"
      4. 断言 options 含 2 项
    Expected Result: 返回构造的突破事件
    Evidence: .sisyphus/evidence/task-4-breakthrough-event.txt

  Scenario: 选择服丹突破
    Tool: Bash (curl)
    Preconditions: 后端运行中, _pending_breakthrough=True
    Steps:
      1. POST /api/v1/game/event/choose option_id="use_pill"
      2. 检查返回结果含 breakthrough info
      3. 检查 _pending_breakthrough 已清除
    Expected Result: 突破结果含 success=True/False，无 _breakthrough_msg 持久化
    Evidence: .sisyphus/evidence/task-4-pill-choice.json

  Scenario: 年龄惩罚生效
    Tool: Bash (uv run pytest)
    Steps:
      1. 测试 calculate_success_rate(age=10) < calculate_success_rate(age=20)
    Expected Result: 低年龄成功率明显降低
    Evidence: .sisyphus/evidence/task-4-age-penalty.txt
  ```

  **Commit**: YES
  - Message: `feat(breakthrough): 突破改为独立特殊事件`
  - Files: `game_service.py`, `breakthrough.py`, `routers/game.py`, `models/event.py`, `tests/`
  - Pre-commit: `uv run pytest tests/test_services/test_breakthrough.py`

- [x] 5. 新增童年/少年期叙事事件 YAML

  **What to do**:
  - **新增 ~12 个 narrative_only YAML 事件**，分为三类:
    - **婴幼儿期 (0-3岁)** — 3个: `childhood_003~005.yaml`
      - 主题: "第一次笑"、"蹒跚学步"、"喃喃自语"
      - min_age: 0, max_age: 3, narrative_only: true, weight: 8-10
    - **童年期 (4-11岁)** — 5个: `childhood_006~010.yaml`
      - 主题: "后山的灵气"、"村里的老道士"、"发现古籍残页"、"捡到奇怪的石头"、"梦中仙人"
      - min_age: 4, max_age: 11, narrative_only: true, weight: 6-8
    - **少年期过渡 (12-16岁)** — 4个: `youth_001~004.yaml`
      - 主题: "踏足修仙"、"拜师学艺"、"初次感知灵力"、"选择前路"
      - min_age: 12, max_age: 16, narrative_only: false (有选项), weight: 5-7
      - cultivation_gain 低 (1-5)
  - 所有新事件遵循现有 YAML schema（参考 `app/data/events/AGENTS.md`）

  **Must NOT do**:
  - 不超过 15 个新事件
  - 不修改现有事件文件
  - 不添加有实质修炼收益的童年事件

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []
  - **Reason**: 内容创作 + YAML 格式遵守，需要创造力

  **Parallelization**:
  - **Can Run In Parallel**: YES (with T1-T4, T6)
  - **Parallel Group**: Wave 1
  - **Blocks**: T14
  - **Blocked By**: T0, T3 (确认 min_age 规范)

  **References**:
  - `app/data/events/AGENTS.md` — 事件模板 schema、分类、新增指南
  - `app/data/events/birth_001.yaml`, `birth_002.yaml` — narrative_only 事件示例
  - `app/data/events/childhood_001.yaml`, `childhood_002.yaml` — 现有童年事件示例
  - 设计评审文档「少年期过渡」建议 — "踏足修仙"、"拜师学艺"主题

  **Acceptance Criteria**:
  - [ ] 新增 ~12 个 YAML 文件，遵循现有 schema
  - [ ] `uv run python -m app.data.validate_data` → PASS
  - [ ] 所有新事件含正确的 trigger_conditions (min_age/max_age)
  - [ ] 婴幼儿/童年事件全部 narrative_only: true
  - [ ] 少年过渡事件有选项但 cultivation_gain <= 5

  **QA Scenarios**:

  ```
  Scenario: YAML 校验通过
    Tool: Bash
    Steps:
      1. `uv run python -m app.data.validate_data`
    Expected Result: 全部 YAML 校验通过（含新增事件）
    Evidence: .sisyphus/evidence/task-5-yaml-validate.txt

  Scenario: 新事件年龄范围正确
    Tool: Bash (grep)
    Steps:
      1. 搜索 childhood_003~005, childhood_006~010, youth_001~004
      2. 确认 min_age/max_age 范围符合设计
    Expected Result: 婴幼儿(0-3), 童年(4-11), 少年(12-16)
    Evidence: .sisyphus/evidence/task-5-age-ranges.txt
  ```

  **Commit**: YES
  - Message: `feat(content): 新增童年/少年期叙事事件`
  - Files: ~12 个新 YAML 文件
  - Pre-commit: `uv run python -m app.data.validate_data`

- [x] 6. 后端 types/models 扩展

  **What to do**:
  - **修改 `app/models/event.py`**:
    - `EventResponse`: 新增 `is_breakthrough: bool = False` 字段
    - `BreakthroughInfo`: 新增 `use_pill: bool | None = None` 字段（记录是否用了丹药）
    - 确保 `AftermathResponse` 已含 `narrative` 和 `breakthrough` 字段（当前已有）
  - 验证 Pydantic 模型可正确序列化

  **Must NOT do**:
  - 不修改前端类型（T7 负责）
  - 不修改路由逻辑（T4 负责）

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - **Reason**: Pydantic 模型微调，小改动

  **Parallelization**:
  - **Can Run In Parallel**: YES (with T1-T5)
  - **Parallel Group**: Wave 1
  - **Blocks**: T4, T7
  - **Blocked By**: T0

  **References**:
  - `app/models/event.py:57-61` — `BreakthroughInfo`: 现有模型定义
  - `app/models/event.py:64-69` — `AftermathResponse`: 确认已有 narrative + breakthrough
  - `app/models/event.py:15-31` — `EventResponse`: 需新增 is_breakthrough

  **Acceptance Criteria**:
  - [ ] `EventResponse` 含 `is_breakthrough` 字段
  - [ ] `BreakthroughInfo` 含 `use_pill` 字段
  - [ ] `uv run pytest` → PASS（无回归）

  **QA Scenarios**:

  ```
  Scenario: 模型序列化正确
    Tool: Bash (uv run pytest)
    Steps:
      1. 创建 EventResponse(is_breakthrough=True, ...)
      2. 序列化为 JSON
      3. 确认含 is_breakthrough 字段
    Expected Result: JSON 输出含新字段
    Evidence: .sisyphus/evidence/task-6-model-serialize.txt
  ```

  **Commit**: YES
  - Message: `refactor(models): 突破事件模型扩展`
  - Files: `app/models/event.py`
  - Pre-commit: `uv run pytest`

- [x] 7. 前端类型扩展 + 后果持久化

  **What to do**:
  - **修改 `web/src/core/types.ts`**:
    - `EventLogEntry.aftermath` L109: 扩展类型添加 `narrative?: string` 和 `breakthrough?: BreakthroughInfo`
    ```typescript
    aftermath: {
      cultivation_change: number;
      age_advance: number;
      narrative?: string;        // 新增
      breakthrough?: BreakthroughInfo;  // 新增
    } | null;
    ```
    - `LoopPhase` L163: 新增 `'breakthrough_choosing'` 阶段
    ```typescript
    export type LoopPhase = 'idle' | 'fetching' | 'typing' | 'waiting_click' | 'choosing' | 'breakthrough_choosing' | 'submitting' | 'aftermath' | 'gameover'
    ```
    - `EventLogEntry.phase`: 新增 `'breakthrough_choosing'`
  - 验证 `vue-tsc --noEmit` 无错误

  **Must NOT do**:
  - 不修改 useGameLoop.ts（T8 负责）
  - 不修改 Vue 组件（T9-T10 负责）
  - 不修改 API client

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []
  - **Reason**: TypeScript 类型系统修改，需仔细处理联合类型

  **Parallelization**:
  - **Can Run In Parallel**: NO (前端基础)
  - **Parallel Group**: Wave 2
  - **Blocks**: T8, T9, T10
  - **Blocked By**: T6

  **References**:
  - `web/src/core/types.ts:103-113` — `EventLogEntry`: aftermath 类型需扩展
  - `web/src/core/types.ts:115-119` — `BreakthroughInfo`: 已有定义
  - `web/src/core/types.ts:121-129` — `ChooseResponse`: aftermath 已含 narrative+breakthrough（前端类型应与此对齐）
  - `web/src/core/types.ts:163` — `LoopPhase`: 需新增阶段

  **Acceptance Criteria**:
  - [ ] `EventLogEntry.aftermath` 含 `narrative` 和 `breakthrough` 可选字段
  - [ ] `LoopPhase` 含 `'breakthrough_choosing'`
  - [ ] `cd web && npx vue-tsc --noEmit` → 零错误

  **QA Scenarios**:

  ```
  Scenario: TypeScript 编译通过
    Tool: Bash
    Steps:
      1. `cd web && npx vue-tsc --noEmit`
    Expected Result: 零错误
    Evidence: .sisyphus/evidence/task-7-tsc-check.txt
  ```

  **Commit**: YES
  - Message: `refactor(frontend): 前端类型扩展 + 后果持久化`
  - Files: `web/src/core/types.ts`
  - Pre-commit: `cd web && npx vue-tsc --noEmit`

- [x] 8. useGameLoop 改造 — 去自动推进 + 突破阶段

  **What to do**:
  - **修改 `web/src/composables/useGameLoop.ts`**:
    - **去掉 2.5s 自动 setTimeout** (L144-149):
      ```typescript
      // 当前 (删除):
      setTimeout(() => {
        entry.phase = 'done'
        advanceEvent()
      }, 2500)
      // 改为:
      entry.phase = 'done'
      setPhase('waiting_click')
      // 用户点击后通过 handleContinueClick() 推进
      ```
    - **新增突破决策阶段**:
      - `handleChoose()` L100-161: 当 `result.aftermath?.breakthrough` 存在时，不再设 `entry.phase = 'breakthrough'`，而是进入新的突破决策流程
      - 突破事件由 `advanceEvent()` 获取（后端返回 `is_breakthrough: true`）
      - 当 `advanceEvent()` 获取到突破事件时: `setPhase('breakthrough_choosing')`, `entry.phase = 'breakthrough_choosing'`
      - `handleChoose()` 处理突破选项时: 选项 id 为 `use_pill` 或 `direct`，发送到 `/event/choose`
    - **修改 `handleContinueClick()`** L163-172:
      - 新增非突破 afternath 的处理: `entry.phase = 'done'` 后推进下一个事件
      - 突破阶段继续由 `handleChoose` 处理
    - **aftermath 持久化**: `handleChoose()` 中将 `result.aftermath` 的 `narrative` 和 `breakthrough` 写入 `entry.aftermath`

  **Must NOT do**:
  - 不修改 GameMain.vue（T9 负责）
  - 不修改 NarrativeLog（T10 负责）
  - 不修改 API client

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: [`test-driven-development`]
  - **Reason**: 前端核心循环重构，涉及阶段机状态转换，需深度推理

  **Parallelization**:
  - **Can Run In Parallel**: YES (with T10, T11)
  - **Parallel Group**: Wave 2
  - **Blocks**: T9, T13
  - **Blocked By**: T4 (后端突破事件), T7 (前端类型)

  **References**:
  - `web/src/composables/useGameLoop.ts:100-161` — `handleChoose()`: 核心处理函数
  - `web/src/composables/useGameLoop.ts:136-141` — 突破分支: 当前设 breakthrough phase
  - `web/src/composables/useGameLoop.ts:144-149` — 2.5s setTimeout: 需删除
  - `web/src/composables/useGameLoop.ts:163-172` — `handleContinueClick()`: 需扩展
  - `web/src/composables/useGameLoop.ts:38-98` — `advanceEvent()`: 需处理突破事件类型
  - `web/src/core/types.ts` (T7 修改后) — 新的 LoopPhase 和 EventLogEntry 类型

  **Acceptance Criteria**:
  - [ ] 代码中无 `setTimeout(() => { advanceEvent() }, 2500)` 或类似自动推进
  - [ ] 普通后果阶段进入 `waiting_click` 等待用户点击
  - [ ] 突破事件触发 `breakthrough_choosing` phase
  - [ ] aftermath.narrative 和 breakthrough 写入 EventLogEntry
  - [ ] `cd web && npx vue-tsc --noEmit` → 零错误

  **QA Scenarios**:

  ```
  Scenario: 普通后果不自动推进
    Tool: Playwright
    Preconditions: 前端运行中, 已开始游戏
    Steps:
      1. 做出一个选择
      2. 等待后果出现
      3. 等待 5 秒
      4. 检查当前仍在 aftermath/waiting_click 阶段
    Expected Result: 5秒后仍停留在后果展示，未自动推进
    Evidence: .sisyphus/evidence/task-8-no-auto-advance.png

  Scenario: 突破事件显示选项
    Tool: Playwright
    Preconditions: 模拟 _pending_breakthrough 状态
    Steps:
      1. 触发突破条件
      2. 获取下一个事件
      3. 确认显示"服用突破丹"和"凭自身实力突破"选项
    Expected Result: 突破事件含 2 个选项按钮
    Evidence: .sisyphus/evidence/task-8-breakthrough-options.png

  Scenario: TypeScript 编译通过
    Tool: Bash
    Steps:
      1. `cd web && npx vue-tsc --noEmit`
    Expected Result: 零错误
    Evidence: .sisyphus/evidence/task-8-tsc.txt
  ```

  **Commit**: YES
  - Message: `feat(loop): 游戏循环改造 — 去自动推进 + 突破阶段`
  - Files: `web/src/composables/useGameLoop.ts`
  - Pre-commit: `cd web && npx vue-tsc --noEmit`

- [x] 9. GameMain.vue 突破选项 + 后果展示改进

  **What to do**:
  - **修改 `web/src/views/GameMain.vue`**:
    - **突破选项渲染** (参考 T11 特效):
      - 当 `phase === 'breakthrough_choosing'` 时，渲染突破选项卡片
      - 使用与普通事件一致的 `OptionCard` 组件
      - 标题: "境界突破"，含突破特有样式
    - **后果展示改进**:
      - 普通 aftermath (L87-100): 显示后果叙事文本 + "点击继续"提示
      - 突破 aftermath: 显示突破结果文本（成功金色 / 失败红色）+ "点击继续"
    - **去掉多余的分支**:
      - 简化当前 L70-86 和 L87-100 的条件渲染
      - 统一 aftermath 处理逻辑
    - **`onGlobalClick()`** L29-35:
      - 在 `waiting_click` 状态下处理普通后果点击推进

  **Must NOT do**:
  - 不修改 useGameLoop.ts（T8 负责）
  - 不修改 CSS 样式文件（T11 负责），仅在 template 中添加 CSS 类名引用

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: []
  - **Reason**: Vue 模板渲染 + UI 展示逻辑

  **Parallelization**:
  - **Can Run In Parallel**: NO (依赖 T8)
  - **Parallel Group**: Wave 2
  - **Blocks**: T13
  - **Blocked By**: T8

  **References**:
  - `web/src/views/GameMain.vue:70-86` — 当前突破 aftermath 渲染
  - `web/src/views/GameMain.vue:87-100` — 当前普通 aftermath 渲染
  - `web/src/views/GameMain.vue:102-109` — 选项卡片渲染: 突破选项复用此模式
  - `web/src/views/GameMain.vue:29-35` — `onGlobalClick()`: 需适配新流程
  - `web/src/components/OptionCard.vue` — 选项卡片组件: 突破选项复用

  **Acceptance Criteria**:
  - [ ] `phase === 'breakthrough_choosing'` 时显示 2 个突破选项
  - [ ] 后果叙事文本在 aftermath 阶段显示
  - [ ] 突破成功/失败有不同视觉风格
  - [ ] "点击继续" 提示在所有 aftermath 阶段出现
  - [ ] `cd web && npx vue-tsc --noEmit` → 零错误

  **QA Scenarios**:

  ```
  Scenario: 突破选项 UI
    Tool: Playwright
    Preconditions: 前端运行中, 处于 breakthrough_choosing 阶段
    Steps:
      1. 截图确认突破选项卡片可见
      2. 确认含"服用突破丹"和"凭自身实力突破"文本
    Expected Result: 2个选项卡片渲染
    Evidence: .sisyphus/evidence/task-9-breakthrough-ui.png

  Scenario: 后果叙事显示
    Tool: Playwright
    Preconditions: 刚做完一个选择
    Steps:
      1. 确认后果叙事文本可见
      2. 确认"点击继续"提示可见
    Expected Result: 后果区域含叙事文本和提示
    Evidence: .sisyphus/evidence/task-9-aftermath-display.png
  ```

  **Commit**: YES
  - Message: `feat(ui): 突破选项UI + 后果展示改进`
  - Files: `web/src/views/GameMain.vue`
  - Pre-commit: `cd web && npx vue-tsc --noEmit`

- [x] 10. NarrativeLog 后果叙事渲染

  **What to do**:
  - **修改 `web/src/components/NarrativeLog.vue`**:
    - L51-56 的后果渲染区域: 新增 `entry.aftermath.narrative` 文本显示
    - 新增突破标记: 当 `entry.aftermath.breakthrough` 存在时显示突破结果标记（小图标或彩色文本）
    - 样式: 后果叙事用较小字号和灰色，与主叙事区分
    - 突破标记用金色文字

  **Must NOT do**:
  - 不修改 useGameLoop.ts
  - 不修改 types.ts（T7 已扩展）

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - **Reason**: 小范围 Vue 模板修改

  **Parallelization**:
  - **Can Run In Parallel**: YES (with T8, T9, T11)
  - **Parallel Group**: Wave 2
  - **Blocks**: T13
  - **Blocked By**: T7

  **References**:
  - `web/src/components/NarrativeLog.vue:51-56` — 后果渲染: 当前仅显示数字
  - `web/src/core/types.ts:103-113` (T7 修改后) — EventLogEntry.aftermath 含 narrative/breakthrough

  **Acceptance Criteria**:
  - [ ] 已完成事件条目显示后果叙事文本
  - [ ] 突破事件在日志中有金色标记
  - [ ] `cd web && npx vue-tsc --noEmit` → 零错误

  **QA Scenarios**:

  ```
  Scenario: 历史日志显示后果叙事
    Tool: Playwright
    Preconditions: 已完成 3+ 个事件
    Steps:
      1. 滚动到已完成事件
      2. 确认条目包含后果叙事文本
    Expected Result: 每个已完成事件下方有灰色后果文字
    Evidence: .sisyphus/evidence/task-10-log-narrative.png
  ```

  **Commit**: YES
  - Message: `feat(ui): NarrativeLog 后果叙事渲染`
  - Files: `web/src/components/NarrativeLog.vue`
  - Pre-commit: `cd web && npx vue-tsc --noEmit`

- [x] 11. 突破仪式感 CSS 特效

  **What to do**:
  - **新增/修改 CSS 样式** (`web/src/styles/`):
    - **突破成功特效**: 全屏金色脉冲 + 文字放大缩放动画
    - **突破失败特效**: 红色闪烁 + 轻微震动效果
    - **突破选项卡片**: 边框发光效果，区别于普通选项
    - 参考现有 `.gm-breakthrough--active` 金色动画样式（已存在但可增强）
  - 所有动画使用 CSS `@keyframes`，不引入 JS 动画库
  - 动画时长 1-2 秒，不过度

  **Must NOT do**:
  - 不添加音效
  - 不引入第三方动画库
  - 不修改组件逻辑（T9 负责）

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: []
  - **Reason**: 纯 CSS 动画效果设计

  **Parallelization**:
  - **Can Run In Parallel**: YES (with T8, T9, T10)
  - **Parallel Group**: Wave 2
  - **Blocks**: —
  - **Blocked By**: T9 (需知道使用哪些 CSS 类名)

  **References**:
  - `web/src/views/GameMain.vue:70-86` — 现有 `.gm-breakthrough--active` 类名
  - `web/src/styles/` — 现有样式文件目录结构
  - 设计评审文档「突破仪式感强化」建议

  **Acceptance Criteria**:
  - [ ] 突破成功有金色脉冲动画
  - [ ] 突破失败有红色闪烁 + 震动
  - [ ] 突破选项卡片有发光边框
  - [ ] 动画时长 ≤ 2秒
  - [ ] `cd web && npx vue-tsc --noEmit` → 零错误（纯 CSS 不影响 TS）

  **QA Scenarios**:

  ```
  Scenario: 突破成功特效
    Tool: Playwright
    Preconditions: 触发突破成功
    Steps:
      1. 截图突破结果展示
      2. 检查 DOM 元素含动画类名
    Expected Result: 金色脉冲动画可见
    Evidence: .sisyphus/evidence/task-11-success-effect.png

  Scenario: 突破失败特效
    Tool: Playwright
    Preconditions: 触发突破失败
    Steps:
      1. 截图突破失败展示
    Expected Result: 红色闪烁效果可见
    Evidence: .sisyphus/evidence/task-11-fail-effect.png
  ```

  **Commit**: YES
  - Message: `feat(ui): 突破仪式感CSS特效`
  - Files: `web/src/styles/` 下的 CSS 文件
  - Pre-commit: `cd web && npx vue-tsc --noEmit`

- [x] 12. 后端测试更新 + 兼容性修复

  **What to do**:
  - **运行 `uv run pytest`** 确认所有 54+ 测试的状态
  - **修复因行为变更导致的失败测试**:
    - 修炼收益相关测试: 适配年龄门控 (age < 12 返回 0)
    - 突破相关测试: 适配新的 pending_breakthrough 流程（不再自动突破）
    - 事件选择测试: 适配新的年龄过滤行为
  - **新增集成测试**:
    - 全生命周期 E2E (`tests/test_e2e.py`): 验证从出生到首次突破的完整路径
    - 边界条件 (`tests/test_edge_cases.py`): 新增 age=3/12/16 的边界测试
  - **目标**: 所有测试通过

  **Must NOT do**:
  - 不修改非测试文件的逻辑（之前任务已改完）
  - 不降低测试覆盖率

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`test-driven-development`]
  - **Reason**: 测试修复和扩展，需要理解所有改动的影响

  **Parallelization**:
  - **Can Run In Parallel**: NO (集成任务)
  - **Parallel Group**: Wave 3
  - **Blocks**: F1-F4
  - **Blocked By**: T1-T6

  **References**:
  - `tests/test_services/test_game_service.py` — 核心服务测试
  - `tests/test_services/test_breakthrough.py` — 突破测试
  - `tests/test_services/test_event_engine.py` — 事件引擎测试
  - `tests/test_e2e.py` — 全生命周期 E2E
  - `tests/test_edge_cases.py` — 边界条件

  **Acceptance Criteria**:
  - [ ] `uv run pytest` → 全部 PASS
  - [ ] 无跳过的测试 (skip/xfail 除外)
  - [ ] 新增 age 边界测试至少 3 个

  **QA Scenarios**:

  ```
  Scenario: 全量测试通过
    Tool: Bash
    Steps:
      1. `uv run pytest -v`
    Expected Result: 全部 PASS，无失败
    Evidence: .sisyphus/evidence/task-12-all-tests.txt

  Scenario: 3岁路径验证
    Tool: Bash (uv run pytest)
    Steps:
      1. 运行新增边界测试
      2. 确认 age=3 时 cultivation_gain=0
    Expected Result: 婴幼儿测试 PASS
    Evidence: .sisyphus/evidence/task-12-age-boundary.txt
  ```

  **Commit**: YES
  - Message: `test(backend): 后端测试更新 + 兼容性修复`
  - Files: `tests/`
  - Pre-commit: `uv run pytest`

- [x] 13. 前端测试更新

  **What to do**:
  - **Vitest 单元测试**:
    - 更新 `useGameLoop` 相关测试: 适配去掉 setTimeout + 新 phase
    - 新增突破阶段状态转换测试
  - **Playwright E2E**:
    - 新增: "创建游戏 → 经历童年叙事 → 少年期 → 首次突破" 完整路径
    - 新增: 后果叙事在历史日志中可见
  - **目标**: 所有前端测试通过

  **Must NOT do**:
  - 不修改组件逻辑
  - 不过度 mock

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`webapp-testing`]
  - **Reason**: 前端测试需要 Playwright 和 Vitest 技能

  **Parallelization**:
  - **Can Run In Parallel**: YES (with T12)
  - **Parallel Group**: Wave 3
  - **Blocks**: F1-F4
  - **Blocked By**: T8-T11

  **References**:
  - `web/src/composables/useGameLoop.ts` — 被 T8 修改后的版本
  - `web/src/views/GameMain.vue` — 被 T9 修改后的版本
  - 现有前端测试目录结构

  **Acceptance Criteria**:
  - [ ] `cd web && npm run test:unit` → PASS
  - [ ] 新增 E2E 测试覆盖完整突破路径
  - [ ] `cd web && npx vue-tsc --noEmit` → 零错误

  **QA Scenarios**:

  ```
  Scenario: 前端单元测试通过
    Tool: Bash
    Steps:
      1. `cd web && npm run test:unit`
    Expected Result: 全部 PASS
    Evidence: .sisyphus/evidence/task-13-unit-tests.txt

  Scenario: E2E 突破路径
    Tool: Bash
    Steps:
      1. `cd web && npm run test:e2e`
    Expected Result: 突破 E2E 测试 PASS
    Evidence: .sisyphus/evidence/task-13-e2e.txt
  ```

  **Commit**: YES
  - Message: `test(frontend): 前端测试更新`
  - Files: `web/tests/` 或等效测试目录
  - Pre-commit: `cd web && npm run test:unit`

- [x] 14. 数据校验 + 文档更新

  **What to do**:
  - **数据校验**: `uv run python -m app.data.validate_data` 确认全部 YAML 通过
  - **AGENTS.md 更新**:
    - 根目录 `AGENTS.md`: 更新"游戏规则"部分（新增生命阶段、突破改为独立事件）
    - `app/services/AGENTS.md`: 新增 `life_stage.py` 模块说明，更新突破流程描述
    - `app/data/events/AGENTS.md`: 新增童年/少年事件说明
    - `web/src/AGENTS.md`: 更新游戏循环阶段描述（新增 breakthrough_choosing）

  **Must NOT do**:
  - 不修改代码逻辑
  - 不修改 README（非必要）

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`markdown-documentation`]
  - **Reason**: 文档更新任务

  **Parallelization**:
  - **Can Run In Parallel**: YES (with T12, T13)
  - **Parallel Group**: Wave 3
  - **Blocks**: —
  - **Blocked By**: T5 (新增事件)

  **References**:
  - `./AGENTS.md` — 根目录知识库
  - `app/services/AGENTS.md` — 服务层知识库
  - `app/data/events/AGENTS.md` — 事件模板知识库
  - `web/src/AGENTS.md` — 前端知识库

  **Acceptance Criteria**:
  - [ ] `uv run python -m app.data.validate_data` → PASS
  - [ ] 4 个 AGENTS.md 文件已更新
  - [ ] 文档准确反映新机制

  **QA Scenarios**:

  ```
  Scenario: 数据校验通过
    Tool: Bash
    Steps:
      1. `uv run python -m app.data.validate_data`
    Expected Result: 全部校验通过
    Evidence: .sisyphus/evidence/task-14-validate.txt
  ```

  **Commit**: YES
  - Message: `chore: 数据校验 + 文档更新`
  - Files: `AGENTS.md`, `app/services/AGENTS.md`, `app/data/events/AGENTS.md`, `web/src/AGENTS.md`
  - Pre-commit: `uv run python -m app.data.validate_data`

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, curl endpoint, run command). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in .sisyphus/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `uv run pytest` + `cd web && npx vue-tsc --noEmit`. Review all changed files for: `as any`/`@ts-ignore`, empty catches, console.log in prod, commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, generic names.
  Output: `Build [PASS/FAIL] | Lint [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real Manual QA** — `unspecified-high` (+ `webapp-testing` skill)
  Start from clean state. Execute EVERY QA scenario from EVERY task — follow exact steps, capture evidence. Test cross-task integration. Test edge cases: newborn game, breakthrough at age 16, aftermath persistence after multiple events. Save to `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff (git log/diff). Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **T0**: `feat(game): Round 3 T1-T9 体验修复 + AGENTS.md 知识库` — 全部改动文件
- **T1**: `feat(core): 引入生命阶段系统 + 修炼年龄门控` — life_stage.py, game_service.py, tests/
- **T2**: `feat(engine): 事件引擎年龄过滤增强` — event_engine.py, tests/
- **T3**: `fix(data): 8个通用事件 min_age 从0改为12` — 8个YAML文件
- **T4**: `feat(breakthrough): 突破改为独立特殊事件` — breakthrough.py, game_service.py, routers/, models/, tests/
- **T5**: `feat(content): 新增童年/少年期叙事事件` — ~12个新YAML文件
- **T6**: `refactor(models): 突破事件模型扩展` — models/event.py
- **T7**: `refactor(frontend): 前端类型扩展 + 后果持久化` — types.ts
- **T8**: `feat(loop): 游戏循环改造 — 去自动推进 + 突破阶段` — useGameLoop.ts
- **T9**: `feat(ui): 突破选项UI + 后果展示改进` — GameMain.vue
- **T10**: `feat(ui): NarrativeLog 后果叙事渲染` — NarrativeLog.vue
- **T11**: `feat(ui): 突破仪式感CSS特效` — styles/
- **T12**: `test(backend): 后端测试更新 + 兼容性修复` — tests/
- **T13**: `test(frontend): 前端测试更新` — web/tests/
- **T14**: `chore: 数据校验 + 文档更新` — validate_data.py, AGENTS.md

---

## Success Criteria

### Verification Commands
```bash
uv run pytest                                                    # Expected: 所有测试 PASS
cd web && npx vue-tsc --noEmit                                   # Expected: 零错误
uv run python -m app.data.validate_data                          # Expected: 所有YAML校验通过
curl -X POST http://localhost:8000/api/v1/game/start -d '...'    # Expected: age=0 的游戏正常创建
```

### Final Checklist
- [ ] 3岁幼儿不触发任何修炼收益事件
- [ ] 突破事件是独立特殊事件，含2个选项
- [ ] 后果叙事在历史日志中可见
- [ ] 正常事件后果不自动推进
- [ ] 突破成功有金色特效
- [ ] 童年/少年期有丰富叙事
- [ ] 54+ 后端测试全通过
- [ ] vue-tsc 零错误
- [ ] 浏览器 E2E 验证通过
