# 重生模拟器 — 后端 MVP 开发计划

## TL;DR

> **核心目标**：构建纯事件驱动修仙文字游戏的后端 API，支撑完整游戏循环（创建角色→抽天赋→逐年事件→结算评分）
>
> **Deliverables**:
> - 6 个 REST API 端点（FastAPI）
> - 28 个事件模板 + 20 张天赋卡 + 3 门派配置
> - DeepSeek AI 叙事生成 + 3 层校验 + 兜底模板
> - SQLite 数据持久化 + AI 缓存
> - 完整 TDD 测试套件（pytest）
>
> **Estimated Effort**: Medium（~3 周单人开发）
> **Parallel Execution**: YES - 5 Waves
> **Critical Path**: 项目骨架 → 境界/天赋数据 → 事件引擎 → AI 服务 → API 端点 → E2E 集成

---

## Context

### Original Request
用户要求为"重生模拟器"AI文字修仙游戏制定后端 MVP 开发计划。前后端分开做 plan，本次只做后端。

### Interview Summary
**Key Discussions**:
- 仓库结构：独立 Git 仓库，非 monorepo
- 测试策略：TDD（Red-Green-Refactor）
- API Key 管理：.env + pydantic-settings
- 认证：无认证，sessionId 标识玩家

**Research Findings**:
- DeepSeek V4-flash 已发布，V3 将于 2026/07/24 弃用 → 使用 `deepseek-v4-flash`
- AI 应只生成叙事文本，后端控制所有数值（与 tech doc 中 AI 返回 consequences 矛盾，已修正）
- AI 缓存 key 应基于 template_id + realm + category（不是完整状态 hash）
- 修为增长公式需自定义（文档未定义）

### Metis Review
**Identified Gaps** (addressed):
- 修为增长公式缺失 → 定义为 `base × (1 + 悟性×0.1) × technique_modifier`
- 门派加入机制模糊 → 脚本化强制事件（10-12岁）
- 每局事件无上限 → 硬上限 60 次
- AI 返回数值 vs 程序控制数值矛盾 → AI 只生成叙事，后端映射选项到预定义后果
- 缓存 key 命中率问题 → 改用 template_id + realm + category
- 僵尸会话问题 → last_active_at + 24h 自动结算
- players 表缺 techniques/inventory 字段 → 补充 JSON TEXT 列
- realm 子阶段表示 → realm_progress 0.0-1.0 浮点映射

---

## Work Objectives

### Core Objective
构建可支撑完整单局游戏的后端 API 系统——从角色创建到人生结算，包含 AI 叙事生成、事件引擎、突破判定、评分结算。

### Concrete Deliverables
- `POST /api/v1/game/start` — 创建新游戏
- `POST /api/v1/game/event` — 获取下一个事件
- `POST /api/v1/game/event/choose` — 玩家做出选择
- `GET /api/v1/game/state/{id}` — 断线恢复
- `POST /api/v1/game/end` — 结算
- `GET /api/v1/leaderboard` — 排行榜
- 28 个事件模板 YAML + 20 张天赋卡数据 + 境界/门派配置
- DeepSeek AI 服务（含 JSON 模式、3 层校验、兜底模板）
- 完整 pytest 测试套件

### Definition of Done
- [ ] `uv run pytest` 全部通过，0 failures
- [ ] 60 次事件完整游戏循环可通过 API 端到端跑通（mock AI）
- [ ] AI 完全不可用时（mock 500），游戏仍可用兜底模板完成
- [ ] 所有 API 响应符合 Pydantic schema 定义
- [ ] 8 种结局均可触发，评分确定性可复现

### Must Have
- TDD：每个功能先写失败测试，再实现
- AI 只生成叙事文本 + 选项文本，后端控制所有数值
- 每个事件模板都有 fallback_narrative（AI 不可用时仍可游戏）
- 游戏逻辑在 services/ 层，零 FastAPI 依赖
- DeepSeek API 封装为可注入/可 mock 的服务
- 所有 API 请求/响应用 Pydantic 模型校验
- 使用同步 sqlite3（非 aiosqlite），FastAPI 线程池处理

### Must NOT Have (Guardrails)
- ❌ 前端代码（Vue/HTML/CSS）
- ❌ 用户认证系统
- ❌ SQLAlchemy/Alembic/ORM
- ❌ Redis/aiosqlite/WebSocket
- ❌ NPC 关系系统、善恶系统、轮回继承
- ❌ 锻体路线、法宝系统
- ❌ 魔道门派、功法融合
- ❌ 微信小游戏适配
- ❌ Docker/部署配置
- ❌ i18n（仅中文）
- ❌ 超过 28 个事件模板或 20 张天赋卡
- ❌ AI 生成游戏状态数值
- ❌ 评分计算使用 AI

---

## Verification Strategy (MANDATORY)

> **ZERO HUMAN INTERVENTION** - ALL verification is agent-executed.

### Test Decision
- **Infrastructure exists**: NO（新项目，TDD 流程中搭建）
- **Automated tests**: YES (TDD)
- **Framework**: pytest + pytest-asyncio + httpx(TestClient)
- **TDD**: 每个任务遵循 RED（失败测试）→ GREEN（最小实现）→ REFACTOR

### QA Policy
Every task MUST include agent-executed QA scenarios.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **API 端点**: Bash (curl) — 发请求，断言状态码 + 响应字段
- **服务层逻辑**: Bash (pytest) — 运行单元测试，断言通过
- **AI 集成**: pytest + mock — mock AI 响应，验证校验/降级逻辑
- **数据完整性**: pytest — 验证 YAML 加载、数值范围、模板覆盖

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation — sequential, 4 tasks):
├── Task 1: 项目骨架 + pyproject.toml + uv 配置 [quick]
├── Task 2: 数据库层 — SQLite 连接 + schema.sql + 4 表建表 [quick]
├── Task 3: Pydantic 数据模型 — 请求/响应 schemas [quick]
└── Task 4: 配置管理 — pydantic-settings + .env [quick]

Wave 2 (Core Data — parallel, 3 tasks):
├── Task 5: 天赋卡系统 — 20 张卡数据 + 抽卡逻辑 [quick]
├── Task 6: 境界系统 — 9 层配置 + 子阶段 + 时间跨度 [quick]
└── Task 7: 门派系统 — 3 门派 + 散修 + 功法配置 [quick]

Wave 3 (Core Engine — partial parallel, 4 tasks):
├── Task 8: 事件引擎 — 模板加载 + 权重选择 + 触发条件 (depends: 6) [deep]
├── Task 9: 突破系统 — 概率计算 + 成功/失败处理 (depends: 5, 6) [deep]
├── Task 10: 评分系统 — 8 结局判定 + 分数 + 等级 (depends: 6) [quick]
└── Task 11: 游戏服务 — 生命周期 + 状态推进 + 修为公式 (depends: 5,6,7,8,9,10) [deep]

Wave 4 (AI + API — sequential, 6 tasks):
├── Task 12: AI 服务 — DeepSeek API 封装 + JSON 模式 + 重试 [unspecified-high]
├── Task 13: AI 输出校验 — 3 层校验 + 兜底模板 (depends: 12) [unspecified-high]
├── Task 14: 缓存服务 — 内存 LRU + SQLite 缓存 (depends: 12) [quick]
├── Task 15: API 端点 — POST /game/start (depends: 11) [quick]
├── Task 16: API 端点 — POST /game/event + /choose (depends: 11, 13) [deep]
└── Task 17: API 端点 — GET /state + POST /end + GET /leaderboard (depends: 11) [quick]

Wave 5 (Data + Integration, 4 tasks):
├── Task 18: 28 个事件模板 YAML 数据 + 启动验证 (depends: 8) [unspecified-high]
├── Task 19: Prompt 模板 — System/User prompt 设计与调优 (depends: 12) [writing]
├── Task 20: 端到端集成测试 — 完整 60 事件游戏循环 (depends: all) [deep]
└── Task 21: 边界 case + AI 降级测试 (depends: 20) [deep]

Wave FINAL (Review — 4 parallel):
├── F1: Plan compliance audit (oracle)
├── F2: Code quality review (unspecified-high)
├── F3: Real manual QA — 10 局完整游戏 (unspecified-high)
└── F4: Scope fidelity check (deep)
→ Present results → Get user okay

Critical Path: T1→T2→T3→T4→T6→T8→T11→T12→T13→T16→T20→F1-F4
Parallel Speedup: ~40% faster than sequential
Max Concurrent: 3 (Wave 2 & 3)
```

### Dependency Matrix

| Task | Depends On | Blocks | Wave |
|------|-----------|--------|------|
| 1 | - | 2,3,4 | 1 |
| 2 | 1 | 8,11 | 1 |
| 3 | 1 | 15-17 | 1 |
| 4 | 1 | 12 | 1 |
| 5 | 1 | 9,11 | 2 |
| 6 | 1 | 8,9,10,11 | 2 |
| 7 | 1 | 11 | 2 |
| 8 | 2,6 | 11,18 | 3 |
| 9 | 5,6 | 11 | 3 |
| 10 | 6 | 11 | 3 |
| 11 | 5,6,7,8,9,10 | 15-17 | 3 |
| 12 | 4 | 13,14,19 | 4 |
| 13 | 12 | 16 | 4 |
| 14 | 12 | 16 | 4 |
| 15 | 3,11 | - | 4 |
| 16 | 3,11,13 | 20 | 4 |
| 17 | 3,11 | - | 4 |
| 18 | 8 | 20 | 5 |
| 19 | 12 | 20 | 5 |
| 20 | all | 21 | 5 |
| 21 | 20 | F1-F4 | 5 |

### Agent Dispatch Summary

- **Wave 1**: 4 tasks → all `quick`
- **Wave 2**: 3 tasks → all `quick`
- **Wave 3**: 4 tasks → T8 `deep`, T9 `deep`, T10 `quick`, T11 `deep`
- **Wave 4**: 6 tasks → T12 `unspecified-high`, T13 `unspecified-high`, T14 `quick`, T15 `quick`, T16 `deep`, T17 `quick`
- **Wave 5**: 4 tasks → T18 `unspecified-high`, T19 `writing`, T20 `deep`, T21 `deep`
- **FINAL**: 4 tasks → F1 `oracle`, F2 `unspecified-high`, F3 `unspecified-high`, F4 `deep`

---

## TODOs

- [x] 1. 项目骨架 + pyproject.toml + uv 配置

  **What to do**:
  - 用 `uv init` 创建 Python 项目，Python 3.11+
  - 配置 `pyproject.toml`：dependencies (fastapi, uvicorn, pydantic, pydantic-settings, python-dotenv, openai, pyyaml, pytest, httpx, pytest-asyncio)
  - 创建 `app/main.py`：FastAPI app 实例 + CORS 中间件 + 健康检查端点 `GET /health`
  - 创建目录结构：`app/models/`, `app/routers/`, `app/services/`, `app/data/`, `tests/`
  - 创建 `app/__init__.py` 和各子目录 `__init__.py`
  - 创建 `.gitignore`（__pycache__, .env, *.db, .venv/）
  - 初始化 Git 仓库

  **Must NOT do**:
  - 不创建 .env 文件（只创建 .env.example）
  - 不添加业务逻辑代码
  - 不配置 Docker

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1 (sequential)
  - **Blocks**: Tasks 2, 3, 4
  - **Blocked By**: None

  **References**:
  - **Pattern**: tech doc §2.2 项目结构 — 参考 `backend/` 目录布局
  - **External**: uv 官方文档 `https://docs.astral.sh/uv/` — 项目初始化和依赖管理
  - **External**: FastAPI 官方文档 `https://fastapi.tiangolo.com/tutorial/` — CORS 中间件配置

  **Acceptance Criteria**:

  **TDD (RED → GREEN)**:
  - [ ] Test: `tests/test_health.py` — `GET /health` 返回 200 + `{"status": "ok"}`

  **QA Scenarios**:

  ```
  Scenario: 项目结构完整性
    Tool: Bash
    Steps:
      1. ls app/ → 包含 main.py, __init__.py, models/, routers/, services/, data/
      2. ls tests/ → 包含 __init__.py, test_health.py
      3. cat pyproject.toml → 包含 fastapi, uvicorn, pytest 依赖
    Expected: 所有目录和文件存在
    Evidence: .sisyphus/evidence/task-1-structure.txt

  Scenario: 健康检查端点
    Tool: Bash (pytest)
    Steps:
      1. uv run pytest tests/test_health.py -v
      2. 断言：test_health_check PASSED
    Expected: 1 passed, 0 failed
    Evidence: .sisyphus/evidence/task-1-health-check.txt

  Scenario: uv 依赖安装成功
    Tool: Bash
    Steps:
      1. uv sync → 成功退出
      2. uv run python -c "import fastapi; print(fastapi.__version__)"
    Expected: 无错误，输出 FastAPI 版本号
    Evidence: .sisyphus/evidence/task-1-deps.txt
  ```

  **Commit**: YES
  - Message: `feat: 初始化项目结构 + uv 配置 + FastAPI 骨架`
  - Files: `pyproject.toml, app/main.py, app/__init__.py, tests/test_health.py, .gitignore, .env.example`

- [x] 2. 数据库层 — SQLite 连接 + schema.sql + 4 表建表

  **What to do**:
  - 创建 `schema.sql`：4 张表（players, event_logs, ai_cache, event_templates）
  - 创建 `app/database.py`：sqlite3 连接工厂 + 启动时执行 schema.sql
  - players 表包含全部字段：id, name, gender, talent_ids, attributes (4列), realm, realm_progress, health, qi, lifespan, faction, spirit_stones, techniques (JSON TEXT), inventory (JSON TEXT), event_count, score, ending_id, is_alive, last_active_at, created_at, updated_at
  - event_logs 表：id, player_id, event_index, event_type, narrative, options (JSON), chosen_option_id, consequences (JSON), created_at
  - ai_cache 表：id, cache_key (template_id+realm+category), response (JSON), hit_count, created_at
  - event_templates 表：id, type, name, min_realm, max_realm, weight, prompt_template, fallback_narrative, default_options (JSON), is_active

  **Must NOT do**:
  - 不使用 SQLAlchemy/ORM
  - 不使用 aiosqlite（同步 sqlite3）
  - 不创建 Alembic 迁移

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1 (sequential, after Task 1)
  - **Blocks**: Tasks 8, 11
  - **Blocked By**: Task 1

  **References**:
  - **Pattern**: tech doc §4.1 SQLite 表结构 — 完整建表 SQL（需补充 techniques/inventory TEXT 字段和 last_active_at 字段）
  - **API**: Python sqlite3 标准库文档 — 同步 API + 连接工厂模式
  - **Metis 建议**: players 表需补充 `techniques TEXT`、`inventory TEXT` 字段；realm_progress 用 0.0-1.0 浮点映射子阶段

  **Acceptance Criteria**:

  **TDD (RED → GREEN)**:
  - [ ] Test: `tests/test_database.py` — 测试数据库初始化（4 表存在 + 列名正确）
  - [ ] Test: 插入/查询 players 表 CRUD 操作
  - [ ] Test: 插入/查询 event_logs 表（外键关联 player）

  **QA Scenarios**:

  ```
  Scenario: Schema 初始化验证
    Tool: Bash (pytest)
    Steps:
      1. uv run pytest tests/test_database.py -v
      2. 验证：4 张表均存在（sqlite_master 查询）
      3. 验证：players 表包含 techniques, inventory, last_active_at 列
    Expected: 所有表和字段存在，测试通过
    Evidence: .sisyphus/evidence/task-2-schema.txt

  Scenario: CRUD 操作
    Tool: Bash (pytest)
    Steps:
      1. 插入 player 记录
      2. 查询返回完整字段
      3. 更新 realm 字段
      4. 删除成功
    Expected: 所有 CRUD 操作正确
    Evidence: .sisyphus/evidence/task-2-crud.txt
  ```

  **Commit**: YES
  - Message: `feat: 数据库层 — SQLite 连接 + schema.sql + 4 表建表`
  - Files: `app/database.py, schema.sql, tests/test_database.py`

- [x] 3. Pydantic 数据模型 — 请求/响应 schemas

  **What to do**:
  - 创建 `app/models/player.py`：PlayerState, Attributes, Technique, Inventory
  - 创建 `app/models/event.py`：EventResponse, EventOption, EventChooseRequest
  - 创建 `app/models/game.py`：GameStartRequest, GameStartResponse, GameEndResponse, LeaderboardEntry
  - 所有模型使用 Pydantic v2 BaseModel + field validators
  - GameStartRequest 校验：attributes 总和 = 10，talent_card_ids 有效（从 20 张卡中选）
  - EventResponse 校验：narrative 长度 20-500 字，options 2-3 个

  **Must NOT do**:
  - 不实现业务逻辑（只定义数据结构）
  - 不连接数据库

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1 (sequential, after Task 1)
  - **Blocks**: Tasks 15-17
  - **Blocked By**: Task 1

  **References**:
  - **Pattern**: tech doc §2.3 前后端数据格式 — 请求/响应 JSON 结构
  - **Pattern**: MVP doc §2.1 玩家存档数据模型 — PlayerState 字段定义
  - **API**: Pydantic v2 文档 — BaseModel, field_validator, model_validator

  **Acceptance Criteria**:

  **TDD (RED → GREEN)**:
  - [ ] Test: `tests/test_models.py` — GameStartRequest 校验（属性总和≠10 → 422）
  - [ ] Test: EventResponse 校验（narrative<20字 → 422）
  - [ ] Test: 所有模型序列化/反序列化正确

  **QA Scenarios**:

  ```
  Scenario: 模型校验
    Tool: Bash (pytest)
    Steps:
      1. uv run pytest tests/test_models.py -v
      2. 验证：有效数据通过校验
      3. 验证：属性总和≠10 报 ValidationError
      4. 验证：空 narrative 报 ValidationError
    Expected: 所有校验测试通过
    Evidence: .sisyphus/evidence/task-3-models.txt
  ```

  **Commit**: YES
  - Message: `feat: Pydantic 数据模型 — 请求/响应 schemas`
  - Files: `app/models/*.py, tests/test_models.py`

- [x] 4. 配置管理 — pydantic-settings + .env

  **What to do**:
  - 创建 `app/config.py`：使用 pydantic-settings BaseSettings
  - 配置项：DEEPSEEK_API_KEY, DEEPSEEK_MODEL (默认 "deepseek-v4-flash"), DEEPSEEK_BASE_URL, DATABASE_PATH, CORS_ORIGINS, MAX_EVENTS_PER_GAME (默认 60), CACHE_TTL (默认 1800)
  - 创建 `.env.example`：列出所有环境变量及说明
  - 创建 `app/dependencies.py`：get_db, get_config, get_ai_service 依赖注入函数

  **Must NOT do**:
  - 不创建实际 .env 文件（含真实 key）
  - 不实现 AI 服务（只定义接口/Protocol）

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1 (sequential, after Task 1)
  - **Blocks**: Task 12
  - **Blocked By**: Task 1

  **References**:
  - **External**: pydantic-settings 文档 — BaseSettings, env_file 配置
  - **Metis 建议**: 使用 deepseek-v4-flash 而非 deepseek-chat/deepseek-v3

  **Acceptance Criteria**:

  **TDD (RED → GREEN)**:
  - [ ] Test: `tests/test_config.py` — 默认值正确（MAX_EVENTS_PER_GAME=60）
  - [ ] Test: .env 文件加载正确
  - [ ] Test: 缺少 DEEPSEEK_API_KEY 时使用默认值不报错（延迟到调用时检查）

  **QA Scenarios**:

  ```
  Scenario: 配置加载
    Tool: Bash (pytest)
    Steps:
      1. uv run pytest tests/test_config.py -v
      2. 验证默认值
      3. 验证环境变量覆盖
    Expected: 配置加载测试通过
    Evidence: .sisyphus/evidence/task-4-config.txt
  ```

  **Commit**: YES
  - Message: `feat: 配置管理 — pydantic-settings + .env`
  - Files: `app/config.py, app/dependencies.py, .env.example, tests/test_config.py`

- [x] 5. 天赋卡系统 — 20 张卡数据 + 抽卡逻辑

  **What to do**:
  - 创建 `app/data/talents.yaml`：20 张天赋卡完整数据（凡品6/灵品6/玄品4/仙品3/神品1）
  - 每张卡：id, name, category, grade, rarity, effect_description, effects (结构化属性加成)
  - 双面卡（血祭之契/天煞孤星/残缺神魂）含 positive_effects + negative_effects
  - 创建 `app/services/talent_service.py`：
    - load_talents() 加载 YAML
    - draw_cards(count=3) 按 rarity 概率抽卡（凡品40%/灵品30%/玄品20%/仙品8%/神品2%）
    - validate_selection(talent_ids) 校验选择的卡是否在抽中列表中
  - 修为增长公式的天赋卡加成部分

  **Must NOT do**:
  - 不实现超过 20 张卡
  - 不实现 UI 展示逻辑

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 6, 7)
  - **Blocks**: Tasks 9, 11
  - **Blocked By**: Task 1

  **References**:
  - **Pattern**: MVP doc §2.4 天赋卡 — 20 张卡完整列表（凡品6/灵品6/玄品4/仙品3/神品1），含双面卡效果
  - **Pattern**: MVP doc §3 抽卡规则 — 抽3张可重抽4次，已丢不回池

  **Acceptance Criteria**:

  **TDD (RED → GREEN)**:
  - [ ] Test: `tests/test_services/test_talent.py` — 加载 20 张卡成功
  - [ ] Test: draw_cards(3) 返回 3 张卡，rarity 分布合理
  - [ ] Test: 双面卡包含 positive + negative effects
  - [ ] Test: 无效 talent_id 校验失败

  **QA Scenarios**:

  ```
  Scenario: 天赋卡数据完整性
    Tool: Bash (pytest)
    Steps:
      1. 加载 talents.yaml → 20 张卡
      2. 每张卡包含 id, name, grade, effects
      3. 双面卡（血祭之契/天煞孤星/残缺神魂）含 negative_effects
    Expected: 20 张卡数据完整
    Evidence: .sisyphus/evidence/task-5-talents.txt

  Scenario: 抽卡概率验证
    Tool: Bash (pytest)
    Steps:
      1. 抽卡 1000 次，统计各品级出现频率
      2. 凡品 ≈ 40%, 灵品 ≈ 30%, 玄品 ≈ 20%, 仙品 ≈ 8%, 神品 ≈ 2%
      3. 每次返回 3 张卡
    Expected: 概率分布在合理范围内（±5%）
    Evidence: .sisyphus/evidence/task-5-draw.txt
  ```

  **Commit**: YES
  - Message: `feat: 天赋卡系统 — 20 张卡数据 + 抽卡逻辑`
  - Files: `app/data/talents.yaml, app/services/talent_service.py, tests/test_services/test_talent.py`

- [ ] 6. 境界系统 — 9 层配置 + 子阶段 + 时间跨度

  **What to do**:
  - 创建 `app/data/realms.yaml`：9 层境界完整配置
  - 每层：name, order, stages[], lifespan, time_span, cultivation_req, spirit_stone_cap, technique_slots
  - 创建 `app/services/realm_service.py`：
    - load_realms() 加载配置
    - get_realm_config(realm_name) 查询配置
    - get_stage_name(realm, progress) → 子阶段名（初/中/后/大圆满）
    - can_breakthrough(cultivation, realm_config) → 判断是否达到突破门槛
    - get_next_realm(current_realm) → 下一境界
  - 子阶段映射：realm_progress 0.0-0.25=初, 0.25-0.5=中, 0.5-0.75=后, 0.75-1.0=大圆满

  **Must NOT do**:
  - 不包含锻体路线（V1.0）
  - 不实现突破概率计算（Task 9）

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 5, 7)
  - **Blocks**: Tasks 8, 9, 10, 11
  - **Blocked By**: Task 1

  **References**:
  - **Pattern**: spec doc §3.1 修灵境界 — 9 层境界完整表（含 v2.0 修正：凡人5年/次）
  - **Pattern**: spec doc §3.5 时间系统 — 各境界时间跨度 + 特殊覆盖
  - **Metis 建议**: realm_progress 用 0.0-1.0 浮点映射子阶段

  **Acceptance Criteria**:

  **TDD (RED → GREEN)**:
  - [ ] Test: `tests/test_services/test_realm.py` — 加载 9 层境界
  - [ ] Test: get_stage_name("金丹", 0.3) → "中期"
  - [ ] Test: get_stage_name("凡人", 0.5) → None（凡人无子阶段）
  - [ ] Test: get_next_realm("练气") → "筑基"
  - [ ] Test: get_next_realm("渡劫/飞升") → None（最高境界）

  **QA Scenarios**:

  ```
  Scenario: 境界数据完整性
    Tool: Bash (pytest)
    Steps:
      1. 加载 realms.yaml → 9 层境界
      2. 每层包含 lifespan, time_span, cultivation_req, technique_slots
      3. 凡人 time_span = 5（v2.0 修正）
    Expected: 9 层境界配置完整
    Evidence: .sisyphus/evidence/task-6-realms.txt

  Scenario: 子阶段映射
    Tool: Bash (pytest)
    Steps:
      1. progress=0.1 → "初期"
      2. progress=0.3 → "中期"
      3. progress=0.6 → "后期"
      4. progress=0.9 → "大圆满"
    Expected: 映射正确
    Evidence: .sisyphus/evidence/task-6-stages.txt
  ```

  **Commit**: YES
  - Message: `feat: 境界系统 — 9 层配置 + 子阶段 + 时间跨度`
  - Files: `app/data/realms.yaml, app/services/realm_service.py, tests/test_services/test_realm.py`

- [ ] 7. 门派系统 — 3 门派 + 散修 + 功法配置

  **What to do**:
  - 创建 `app/data/sects.yaml`：3 个正道门派 + 散修
  - 每个门派：name, type(正道), weapon, attribute(金/水/土), join_conditions, techniques[{name, grade, attribute, level}]
  - 门派加入条件：万剑山庄(根骨≥3或悟性≥3)，逍遥派(悟性≥4)，金刚寺(根骨≥4+心性≥3)
  - 创建 `app/services/sect_service.py`：
    - load_sects() 加载配置
    - check_join_conditions(player_attributes, sect_name) → bool
    - get_sect_techniques(sect_name) → 功法列表
  - 门派加入为脚本化强制事件（10-12岁触发），不是随机

  **Must NOT do**:
  - 不包含魔道门派
  - 不实现隐秘传承
  - 不实现门派贡献/任务系统

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 5, 6)
  - **Blocks**: Task 11
  - **Blocked By**: Task 1

  **References**:
  - **Pattern**: MVP doc §4 门派设计 — 万剑山庄/逍遥派/金刚寺完整设定
  - **Metis 建议**: 门派加入为强制脚本事件（10-12岁），非随机触发

  **Acceptance Criteria**:

  **TDD (RED → GREEN)**:
  - [ ] Test: `tests/test_services/test_sect.py` — 加载 4 条路线（3 门派 + 散修）
  - [ ] Test: 万剑山庄加入条件（根骨=3 通过，根骨=2+悟性=2 不通过）
  - [ ] Test: 金刚寺双条件（根骨≥4+心性≥3）
  - [ ] Test: 散修无加入条件

  **QA Scenarios**:

  ```
  Scenario: 门派数据完整性
    Tool: Bash (pytest)
    Steps:
      1. 加载 sects.yaml → 3 门派 + 散修
      2. 每个门派包含入门功法（灵品）
    Expected: 配置完整
    Evidence: .sisyphus/evidence/task-7-sects.txt
  ```

  **Commit**: YES
  - Message: `feat: 门派系统 — 3 门派 + 散修 + 功法配置`
  - Files: `app/data/sects.yaml, app/services/sect_service.py, tests/test_services/test_sect.py`

- [ ] 8. 事件引擎 — 模板加载 + 权重选择 + 触发条件

  **What to do**:
  - 创建 `app/services/event_engine.py`：
    - load_templates() 从 app/data/events/ 加载所有 YAML
    - filter_templates(player_state) → 筛选可用事件（境界/年龄/门派条件）
    - calculate_weights(filtered_templates, player_state) → 按公式计算权重
    - select_event(weighted_templates) → 加权随机选择
    - build_event_context(event_template, player_state) → 构建 AI 输入上下文
  - 权重公式：日常=1.0, 奇遇=0.3+气运×0.05, 瓶颈=0.5+(修为/突破门槛)×0.5
  - 每 N 次日常后强制插入非日常事件
  - 事件触发条件：min_realm, max_realm, min_age, max_age, required_faction
  - 创建 1-2 个测试用事件模板 YAML 用于开发

  **Must NOT do**:
  - 不实现 28 个完整模板（Task 18）
  - 不调用 AI 服务（只准备上下文）
  - 不实现事件链 flag 系统（V1.0）

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 9, 10)
  - **Blocks**: Tasks 11, 18
  - **Blocked By**: Tasks 2, 6

  **References**:
  - **Pattern**: tech doc §2.1 事件模板格式（YAML）— id, type, trigger_conditions, weight, prompt_template, fallback_narrative, default_options
  - **Pattern**: spec doc §6.2 事件触发逻辑 — 权重公式 + 筛选流程
  - **Metis 建议**: 确保每个境界至少有 1 个通用日常事件（防卡死）

  **Acceptance Criteria**:

  **TDD (RED → GREEN)**:
  - [ ] Test: `tests/test_services/test_event_engine.py` — 模板加载成功
  - [ ] Test: 境界筛选（金丹事件不出现在练气筛选结果中）
  - [ ] Test: 权重计算正确（日常1.0, 奇遇=0.3+气运×0.05）
  - [ ] Test: 强制非日常事件（连续 N 次日常后触发）
  - [ ] Test: 空模板池返回通用兜底事件

  **QA Scenarios**:

  ```
  Scenario: 事件筛选边界
    Tool: Bash (pytest)
    Steps:
      1. player realm="凡人" → 只返回凡人可用事件
      2. player realm="元婴" → 不返回凡人限定事件
      3. player 无门派 → 不返回 requires_faction 事件
    Expected: 筛选结果正确
    Evidence: .sisyphus/evidence/task-8-filter.txt
  ```

  **Commit**: YES
  - Message: `feat: 事件引擎 — 模板加载 + 权重选择 + 触发条件`
  - Files: `app/services/event_engine.py, app/data/events/_test_daily.yaml, tests/test_services/test_event_engine.py`

- [ ] 9. 突破系统 — 概率计算 + 成功/失败处理

  **What to do**:
  - 创建 `app/services/breakthrough.py`：
    - calculate_success_rate(player_state) → 成功率（0-100%）
    - 公式：基础50% + 根骨×5% + 悟性×3% + 心性×2% - 境界跨级惩罚
    - attempt_breakthrough(player_state, use_pill=False) → BreakthroughResult(success, new_realm, cultivation_loss, realm_drop)
    - 成功：境界提升，修为重置为 realm_progress=0
    - 失败：修为损失 20-50%（百折不挠天赋可减免 -10%），10% 概率境界跌落
    - 筑基丹：筑基突破必需 + 成功率+15%
    - 突破丹：成功率+15%
    - 渡劫成功 → 触发飞升结局（不是境界提升）

  **Must NOT do**:
  - 不实现锻体突破
  - 不实现心魔劫（V1.0）

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 8, 10)
  - **Blocks**: Task 11
  - **Blocked By**: Tasks 5, 6

  **References**:
  - **Pattern**: MVP doc §6.2 突破系统 — 成功率公式 + 失败后果
  - **Pattern**: spec doc §3.4 突破三重条件 — 修为门槛 + 概率判定 + 机缘/资源

  **Acceptance Criteria**:

  **TDD (RED → GREEN)**:
  - [ ] Test: 全 0 属性 → 成功率 = 50%（基础值）
  - [ ] Test: 全 10 根骨 → 成功率 = 50%+10×5% = 100%（capped at 95%）
  - [ ] Test: 突破成功 → realm 提升 + cultivation 重置
  - [ ] Test: 突破失败 → cultivation 损失 20-50%
  - [ ] Test: 突破丹 +15%
  - [ ] Test: 百折不挠天赋 → 损失减免 10%
  - [ ] Test: 渡劫成功 → 触发飞升结局标志

  **QA Scenarios**:

  ```
  Scenario: 突破概率边界值
    Tool: Bash (pytest)
    Steps:
      1. 根骨=0,悟性=0,心性=0 → rate=50%
      2. 根骨=10,悟性=10,心性=10 → rate=50+50+30+20=120%, capped=95%
      3. use_pill=True → rate+15%
    Expected: 概率计算正确，上限 95%
    Evidence: .sisyphus/evidence/task-9-breakthrough.txt
  ```

  **Commit**: YES
  - Message: `feat: 突破系统 — 概率计算 + 成功/失败处理`
  - Files: `app/services/breakthrough.py, tests/test_services/test_breakthrough.py`

- [ ] 10. 评分系统 — 8 结局判定 + 分数 + 等级

  **What to do**:
  - 创建 `app/services/scoring.py`：
    - determine_ending(player_state) → 8 种结局之一
    - 8 结局：飞升成仙/功德圆满/魔道至尊/战死/走火/寿终/意外/道心破碎
    - MVP 结局判定：飞升(渡劫成功), 寿终(年龄≥寿命), 其余简化为默认
    - calculate_score(player_state, ending) → 0-100 分
    - MVP 评分：境界50% + 寿命20% + 功法20% + 结局10%
    - get_grade(score) → SSS/SS/S/A/B/C/D
    - 评分 = 纯算术，无 AI 参与，确定性可复现

  **Must NOT do**:
  - 不使用完整 8 维度评分（MVP 只用 4 维度）
  - 不调用 AI 生成评语（那是结算 API 的事）

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 8, 9)
  - **Blocks**: Task 11
  - **Blocked By**: Task 6

  **References**:
  - **Pattern**: spec doc §12.1 MVP 评分 — 4 维度权重（境界50%/寿命20%/功法20%/结局10%）
  - **Pattern**: spec doc §12.3 8 种结局 — 触发条件

  **Acceptance Criteria**:

  **TDD (RED → GREEN)**:
  - [ ] Test: 大乘+渡劫成功 → 结局="飞升成仙"
  - [ ] Test: 年龄≥寿命 → 结局="寿终正寝"
  - [ ] Test: 相同状态调用两次 → 分数完全相同（确定性）
  - [ ] Test: 境界=凡人 → 分数很低
  - [ ] Test: score=95 → grade="SSS", score=25 → grade="D"

  **QA Scenarios**:

  ```
  Scenario: 评分等级映射
    Tool: Bash (pytest)
    Steps:
      1. score=0 → "D"
      2. score=50 → "B"
      3. score=100 → "SSS"
    Expected: 等级映射正确
    Evidence: .sisyphus/evidence/task-10-scoring.txt
  ```

  **Commit**: YES
  - Message: `feat: 评分系统 — 8 结局判定 + 分数 + 等级`
  - Files: `app/services/scoring.py, tests/test_services/test_scoring.py`

- [ ] 11. 游戏服务 — 生命周期 + 状态推进 + 修为公式

  **What to do**:
  - 创建 `app/services/game_service.py`：
    - start_game(name, gender, talent_card_ids, attributes) → 创建游戏，返回 sessionId + 初始状态
    - get_next_event(session_id) → 调用事件引擎 + AI 服务 → 返回事件叙事+选项
    - process_choice(session_id, option_id) → 结算选择后果 + 推进时间 + 更新状态
    - get_state(session_id) → 查询当前状态
    - end_game(session_id) → 调用评分系统 + AI 评语 → 返回结算结果
    - check_game_over(player_state) → 判断是否游戏结束（年龄≥寿命/事件≥60/飞升）
  - 修为增长公式：`cultivation_gain = base × (1 + comprehension × 0.1) × technique_modifier`
    - base 按事件类型：日常=10, 奇遇=30, 瓶颈=5
    - technique_modifier：无功法=0.5, 凡品=1.0, 灵品=1.5, 玄品=2.0, 仙品=3.0
  - 状态推进：age += realm_config.time_span
  - 灵石上限检查：spirit_stones = min(spirit_stones, realm_config.spirit_stone_cap)
  - 修为溢出处理：超出部分带入下一境界进度

  **Must NOT do**:
  - 不直接调用 DeepSeek API（通过 ai_service 间接调用）
  - 不实现前端展示逻辑

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (after Tasks 5-10)
  - **Blocks**: Tasks 15-17
  - **Blocked By**: Tasks 5, 6, 7, 8, 9, 10

  **References**:
  - **Pattern**: tech doc §2.1 API 设计 — 6 个端点的请求/响应格式
  - **Metis 建议**: 修为增长公式定义为 `base × (1 + 悟性×0.1) × technique_modifier`
  - **Metis 建议**: 修为溢出部分带入下一境界进度
  - **Metis 建议**: 灵石不足时扣费选项效果降低或灰色

  **Acceptance Criteria**:

  **TDD (RED → GREEN)**:
  - [ ] Test: start_game → 返回有效 sessionId + age=0, realm="凡人"
  - [ ] Test: process_choice → cultivation 增加, age 推进
  - [ ] Test: 修为公式正确（悟性=5 → ×1.5）
  - [ ] Test: 灵石上限检查（超过上限被截断）
  - [ ] Test: check_game_over → 年龄≥寿命=True
  - [ ] Test: check_game_over → event_count≥60=True

  **QA Scenarios**:

  ```
  Scenario: 完整状态推进
    Tool: Bash (pytest)
    Steps:
      1. start_game → 初始状态
      2. 模拟 1 次选择 → cultivation 增加, age 推进 time_span
      3. 灵石变动正确
      4. 事件计数 +1
    Expected: 状态推进正确
    Evidence: .sisyphus/evidence/task-11-game-service.txt
  ```

  **Commit**: YES
  - Message: `feat: 游戏服务 — 生命周期 + 状态推进 + 修为公式`
  - Files: `app/services/game_service.py, tests/test_services/test_game_service.py`

- [ ] 12. AI 服务 — DeepSeek API 封装 + JSON 模式 + 重试

  **What to do**:
  - 创建 `app/services/ai_service.py`：
    - 定义 `AIServiceProtocol`（Protocol 类）：generate_event(prompt, context) → AIResponse
    - 实现 `DeepSeekService`：
      - 使用 openai SDK，base_url="https://api.deepseek.com"
      - model="deepseek-v4-flash"
      - response_format={"type": "json_object"} 强制 JSON 输出
      - 重试逻辑：最多 2 次，指数退避（1s, 3s）
      - 空 content 处理（已知 DeepSeek 偶发）：重试一次
    - 实现 `MockAIService`（测试用）：返回预设 JSON
  - 所有 AI 调用通过 Protocol 接口，可在 dependency_overrides 中替换

  **Must NOT do**:
  - 不让 AI 生成数值（AI 只生成 narrative + option texts）
  - 不实现流式输出（回合制不需要 SSE）
  - 不在此实现输出校验（Task 13 负责）

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4 (first in wave)
  - **Blocks**: Tasks 13, 14, 19
  - **Blocked By**: Task 4

  **References**:
  - **External**: DeepSeek API 文档 — openai SDK 兼容模式, JSON mode
  - **External**: openai Python SDK — base_url 参数, response_format
  - **Metis 建议**: 使用 deepseek-v4-flash，处理空 content 已知问题

  **Acceptance Criteria**:

  **TDD (RED → GREEN)**:
  - [ ] Test: MockAIService.generate_event → 返回有效 JSON
  - [ ] Test: DeepSeekService 500 错误 → 重试 2 次
  - [ ] Test: DeepSeekService 空 content → 重试一次
  - [ ] Test: dependency_overrides 替换 AI 服务成功

  **QA Scenarios**:

  ```
  Scenario: AI 服务可替换
    Tool: Bash (pytest)
    Steps:
      1. app.dependency_overrides[get_ai_service] = MockAIService
      2. 调用 API → 返回 mock 数据
      3. 不发起真实 HTTP 请求
    Expected: mock 成功替换
    Evidence: .sisyphus/evidence/task-12-ai-mock.txt
  ```

  **Commit**: YES
  - Message: `feat: AI 服务 — DeepSeek API 封装 + JSON 模式 + 重试`
  - Files: `app/services/ai_service.py, tests/test_services/test_ai_service.py`

- [ ] 13. AI 输出校验 — 3 层校验 + 兜底模板

  **What to do**:
  - 创建 `app/services/ai_validator.py`：
    - **第 1 层 JSON 解析**：去除 markdown 代码块标记，修复常见格式错误
    - **第 2 层 JSON Schema 校验**：narrative 20-500 字，options 2-3 个，每个 option 含 id + text
    - **第 3 层内容安全**：禁用词黑名单（手机/电脑/微信/枪/炮/道侣/善恶值/法宝/锻体/轮回）
    - 数值裁剪：如果 AI 返回了数值字段，忽略/删除（后端控制数值）
    - 兜底逻辑：校验失败 → 使用模板的 fallback_narrative + default_options
  - 所有校验函数为纯函数（无副作用，可独立测试）

  **Must NOT do**:
  - 不让校验层生成数值
  - 不修改游戏状态

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Task 14, after Task 12)
  - **Blocks**: Task 16
  - **Blocked By**: Task 12

  **References**:
  - **Pattern**: tech doc §3.2 AI 输出校验 — 3 层防护
  - **Metis 建议**: Prompt 白名单列出 MVP 系统 + 黑名单列出非 MVP 概念

  **Acceptance Criteria**:

  **TDD (RED → GREEN)**:
  - [ ] Test: 有效 JSON 通过校验
  - [ ] Test: markdown 包裹的 JSON 解析成功
  - [ ] Test: narrative<20 字 → 校验失败 → 返回兜底
  - [ ] Test: 禁用词检测（含"微信" → 过滤）
  - [ ] Test: AI 返回数值字段 → 被删除
  - [ ] Test: options<2 → 从 default_options 补齐

  **Commit**: YES
  - Message: `feat: AI 输出校验 — 3 层校验 + 兜底模板`
  - Files: `app/services/ai_validator.py, tests/test_services/test_ai_validator.py`

- [ ] 14. 缓存服务 — 内存 LRU + SQLite 缓存

  **What to do**:
  - 创建 `app/services/cache_service.py`：
    - 内存 LRU 缓存（collections.OrderedDict，最大 100 条）
    - SQLite ai_cache 表持久化
    - cache_key = f"{template_id}:{realm}:{category}"（非完整状态 hash）
    - get_cached(template_id, realm, category) → Optional[response]
    - set_cached(template_id, realm, category, response)
    - TTL 30 分钟
  - 双层查找：内存 → SQLite → 未命中

  **Must NOT do**:
  - 不使用 Redis
  - 不缓存完整状态相关的结果

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Task 13, after Task 12)
  - **Blocks**: Task 16
  - **Blocked By**: Task 12

  **References**:
  - **Pattern**: tech doc §3.4 降级兜底 — 缓存查找优先于 AI 调用
  - **Metis 建议**: cache_key 改为 template_id + realm + category（非状态 hash）

  **Acceptance Criteria**:

  **TDD (RED → GREEN)**:
  - [ ] Test: 首次查询 → miss
  - [ ] Test: 写入后查询 → hit
  - [ ] Test: 超过 TTL → miss
  - [ ] Test: LRU 淘汰（超过 100 条）
  - [ ] Test: SQLite 持久化（内存未命中 → SQLite 命中）

  **Commit**: YES
  - Message: `feat: 缓存服务 — 内存 LRU + SQLite 缓存`
  - Files: `app/services/cache_service.py, tests/test_services/test_cache_service.py`

- [ ] 15. API 端点 — POST /game/start 创建游戏

  **What to do**:
  - 在 `app/routers/game.py` 实现 POST /api/v1/game/start
  - 接收：name, gender, talent_card_ids (3个), attributes (根骨/悟性/心性/气运, 总和=10)
  - 处理：校验 → 抽卡确认 → 初始化玩家状态 → 写入数据库 → 返回 sessionId + initialState
  - 初始状态：age=0, realm="凡人", cultivation=0, lifespan=80, health=100, qi=100, spirit_stones=0, techniques=[], inventory={}, sect=null

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**: Wave 4, depends on Tasks 3, 11

  **Acceptance Criteria**:

  **TDD (RED → GREEN)**:
  - [ ] Test: 正常请求 → 201 + sessionId + 完整初始状态
  - [ ] Test: 属性总和≠10 → 422
  - [ ] Test: talent_card_ids 无效 → 422
  - [ ] Test: 数据库 players 表有新记录

  **QA Scenarios**:

  ```
  Scenario: 创建游戏端到端
    Tool: Bash (curl)
    Steps:
      1. curl -X POST -H "Content-Type: application/json" -d '{"name":"测试仙人","gender":"男","talent_card_ids":["f01","l02","x01"],"attributes":{"rootBone":3,"comprehension":3,"mindset":2,"luck":2}}' http://localhost:8000/api/v1/game/start
      2. 断言：200 + sessionId(UUID) + state.realm="凡人"
    Expected: 游戏创建成功
    Evidence: .sisyphus/evidence/task-15-start.txt
  ```

  **Commit**: YES
  - Message: `feat: API — POST /game/start 创建游戏端点`
  - Files: `app/routers/game.py, tests/test_api/test_game_start.py`

- [ ] 16. API 端点 — POST /game/event + /choose 事件端点

  **What to do**:
  - POST /api/v1/game/event：
    - 接收 sessionId
    - 流程：查状态 → 检查游戏是否结束 → 事件引擎选事件 → 查缓存 → 调 AI（miss 时）→ 校验 AI 输出 → 返回 narrative + options
    - 返回 metadata.isFallback 标记
  - POST /api/v1/game/event/choose：
    - 接收 sessionId + optionId
    - 流程：查当前事件 → 映射 optionId 到预定义后果 → 结算（cultivation/age/spirit_stones/health/qi）→ 检查突破 → 检查游戏结束 → 写入 event_logs → 返回 newState + aftermath
    - aftermath 包含：所有属性变化明细 + 突破结果（如有）

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**: Wave 4, depends on Tasks 3, 11, 13

  **Acceptance Criteria**:

  **TDD (RED → GREEN)**:
  - [ ] Test: 正常 event → 200 + narrative + 2-3 options
  - [ ] Test: 正常 choose → 200 + newState（cultivation 变化, age 推进）
  - [ ] Test: 已结束游戏 event → 400
  - [ ] Test: 无效 optionId → 400
  - [ ] Test: AI 降级 → fallback_narrative + metadata.isFallback=true
  - [ ] Test: 突破触发 → response 包含 breakthrough_result

  **QA Scenarios**:

  ```
  Scenario: 事件-选择循环
    Tool: Bash (pytest via TestClient)
    Steps:
      1. 创建游戏 → 获取 sessionId
      2. POST /event → 获取 narrative + options
      3. POST /choose optionId=options[0].id → 获取 newState
      4. 验证 cultivation > 0, age > 0
    Expected: 完整事件循环工作
    Evidence: .sisyphus/evidence/task-16-event-loop.txt
  ```

  **Commit**: YES
  - Message: `feat: API — POST /game/event + /choose 事件端点`
  - Files: `app/routers/game.py (updated), tests/test_api/test_event_flow.py`

- [ ] 17. API 端点 — GET /state + POST /end + GET /leaderboard

  **What to do**:
  - GET /api/v1/game/state/{id}：查询玩家完整状态（断线恢复）
  - POST /api/v1/game/end：
    - 调用 scoring.determine_ending → 结局类型
    - 调用 scoring.calculate_score → 分数 + 等级
    - 调用 AI 生成人生评语（200-300 字）
    - 设置 is_alive=false → 返回结算结果
    - 已结束游戏 → 400
  - GET /api/v1/leaderboard：
    - 查询 players WHERE is_alive=false ORDER BY score DESC LIMIT 10
    - 返回 [{rank, name, score, grade, ending, realm, lifespan}]

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**: Wave 4, depends on Tasks 3, 11

  **Acceptance Criteria**:

  **TDD (RED → GREEN)**:
  - [ ] Test: GET /state → 完整玩家状态
  - [ ] Test: GET /state 无效 id → 404
  - [ ] Test: POST /end → 结算结果（score + grade + ending + ai_commentary）
  - [ ] Test: POST /end 已结束 → 400
  - [ ] Test: GET /leaderboard → 按 score 降序，最多 10 条
  - [ ] Test: GET /leaderboard 空库 → 200 + []

  **Commit**: YES
  - Message: `feat: API — GET /state + POST /end + GET /leaderboard`
  - Files: `app/routers/game.py (updated), tests/test_api/test_state_end_leaderboard.py`

- [ ] 18. 28 个事件模板 YAML 数据 + 启动验证

  **What to do**:
  - 创建 `app/data/events/` 目录下 28 个 YAML 文件：
    - daily_001.yaml ~ daily_015.yaml（日常15个）
    - adventure_001.yaml ~ adventure_008.yaml（奇遇8个）
    - bottleneck_001.yaml ~ bottleneck_005.yaml（瓶颈5个）
  - 每个 YAML 包含完整字段：id, type, name, min_realm, max_realm, min_age, max_age, weight, requires_faction(bool), prompt_template, fallback_narrative, default_options(2-3个含 consequence)
  - 创建 `app/data/validate_data.py`：启动时校验所有 YAML 完整性
  - 确保**每个境界至少有 1 个通用日常事件**（防卡死）
  - 门派加入事件：bottleneck_000_special_sect.yaml（10-12岁强制触发）

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**: Wave 5, depends on Task 8

  **References**:
  - **Pattern**: MVP doc §3 事件模板清单 — 28 个事件完整列表（D01-D15, Q01-Q08, P01-P05）
  - **Pattern**: tech doc §4.2 事件模板格式（YAML）— 结构示例
  - **Metis 建议**: 门派加入为脚本化强制事件

  **Acceptance Criteria**:

  **TDD (RED → GREEN)**:
  - [ ] Test: 加载 28 个模板全部成功
  - [ ] Test: 每个模板包含 fallback_narrative + default_options
  - [ ] Test: 每个境界至少有 1 个可用日常事件
  - [ ] Test: 启动校验函数 detect 格式错误

  **Commit**: YES
  - Message: `feat: 28 个事件模板 YAML 数据 + 启动验证`
  - Files: `app/data/events/*.yaml, app/data/validate_data.py, tests/test_data/test_events.py`

- [ ] 19. Prompt 模板 — System/User prompt 设计

  **What to do**:
  - 创建 `app/data/prompts/system.yaml`：System Prompt 模板
    - 角色设定：修仙世界叙事大师
    - 输出格式约束：严格 JSON
    - MVP 系统白名单：境界/功法/灵石/门派/丹药(突破丹+筑基丹)/天赋卡
    - 非 MVP 概念黑名单：禁止提及道侣/善恶值/法宝/锻体/轮回/心魔劫/赛季
    - 叙事规则：符合修仙世界观、选项有意义、避免现代用语
  - 创建 `app/data/prompts/user.yaml`：User Prompt 模板
    - 当前玩家状态占位符
    - 事件模板占位符
    - 最近 5 个事件摘要占位符
  - Prompt 总长度控制在 ~700 tokens（System ~400 + User ~300）

  **Recommended Agent Profile**:
  - **Category**: `writing`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**: Wave 5, depends on Task 12

  **Acceptance Criteria**:

  **TDD (RED → GREEN)**:
  - [ ] Test: Prompt 模板加载成功
  - [ ] Test: 占位符替换后生成完整 prompt
  - [ ] Test: 黑名单词汇不出现在 System prompt 的允许列表中

  **Commit**: YES
  - Message: `feat: Prompt 模板 — System/User prompt 设计`
  - Files: `app/data/prompts/system.yaml, app/data/prompts/user.yaml, tests/test_data/test_prompts.py`

- [ ] 20. 端到端集成测试 — 完整 60 事件游戏循环

  **What to do**:
  - 创建 `tests/test_e2e.py`：
    - 完整游戏循环：start → (event → choose) × 60 → end
    - 验证：每一步状态推进正确、最终结算正确
    - 验证：event_count=60 时自动触发结束
    - 验证：AI mock 正确工作
    - 验证：所有 API 端点协作正确
  - 运行多个属性组合的 E2E 测试

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**: Wave 5, depends on all previous tasks

  **Acceptance Criteria**:

  **TDD (RED → GREEN)**:
  - [ ] Test: 完整 60 事件游戏循环通过
  - [ ] Test: 不同属性组合 ×3 均可完成
  - [ ] Test: 最终 score 为确定性值
  - [ ] Test: `uv run pytest tests/test_e2e.py` → ALL PASS

  **Commit**: YES
  - Message: `test: 端到端集成测试 — 完整 60 事件游戏循环`
  - Files: `tests/test_e2e.py`

- [ ] 21. 边界 case + AI 降级测试

  **What to do**:
  - 创建 `tests/test_edge_cases.py`：
    - 全 0 属性（0/0/0/10）：游戏完成，突破基础 50%
    - 全 10 单属性（10/0/0/0）：游戏完成
    - 双面天赋卡（血祭之契）：正负效果均应用
    - 散修路线全程：无门派，功法来源不同
    - AI 500 → 兜底模板全程可用
    - AI 返回空 content → 重试 → 兜底
    - AI 返回无效 JSON → 校验失败 → 兜底
    - 零灵石全程：不崩溃
    - 超过寿命上限：触发"寿终正寝"

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**: Wave 5, depends on Task 20

  **Acceptance Criteria**:

  **TDD (RED → GREEN)**:
  - [ ] Test: 所有边界 case 通过
  - [ ] Test: AI 降级场景游戏仍可完成
  - [ ] Test: `uv run pytest tests/test_edge_cases.py` → ALL PASS

  **Commit**: YES
  - Message: `test: 边界 case + AI 降级测试`
  - Files: `tests/test_edge_cases.py`

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, run test). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in .sisyphus/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `uv run pytest` + ruff/mypy. Review all changed files for: `Any` type, empty except, print() in prod, commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, generic names. Verify services/ has zero FastAPI imports.
  Output: `Build [PASS/FAIL] | Lint [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real Manual QA** — `unspecified-high`
  Start from clean state (`uv run uvicorn app.main:app`). Execute EVERY QA scenario from EVERY task — follow exact steps, capture evidence. Run 10 complete games via curl. Test edge cases: all-0 attributes, all-10 attributes, freelance path, double-edged cards, AI-down scenario. Save to `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff (git log/diff). Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance. Detect cross-task contamination. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

| Wave | Commit | Message | Files |
|------|--------|---------|-------|
| 1 | 1 | `feat: 初始化项目结构 + uv 配置 + FastAPI 骨架` | pyproject.toml, app/main.py, app/__init__.py |
| 1 | 2 | `feat: 数据库层 — SQLite 连接 + schema.sql + 4 表建表` | app/database.py, schema.sql |
| 1 | 3 | `feat: Pydantic 数据模型 — 请求/响应 schemas` | app/models/*.py |
| 1 | 4 | `feat: 配置管理 — pydantic-settings + .env` | app/config.py, .env.example |
| 2 | 5 | `feat: 天赋卡系统 — 20 张卡数据 + 抽卡逻辑` | app/data/talents.yaml, app/services/talent_service.py |
| 2 | 6 | `feat: 境界系统 — 9 层配置 + 子阶段 + 时间跨度` | app/data/realms.yaml, app/services/realm_service.py |
| 2 | 7 | `feat: 门派系统 — 3 门派 + 散修 + 功法配置` | app/data/sects.yaml, app/services/sect_service.py |
| 3 | 8 | `feat: 事件引擎 — 模板加载 + 权重选择 + 触发条件` | app/services/event_engine.py |
| 3 | 9 | `feat: 突破系统 — 概率计算 + 成功/失败处理` | app/services/breakthrough.py |
| 3 | 10 | `feat: 评分系统 — 8 结局判定 + 分数 + 等级` | app/services/scoring.py |
| 3 | 11 | `feat: 游戏服务 — 生命周期 + 状态推进 + 修为公式` | app/services/game_service.py |
| 4 | 12 | `feat: AI 服务 — DeepSeek API 封装 + JSON 模式` | app/services/ai_service.py |
| 4 | 13 | `feat: AI 输出校验 — 3 层校验 + 兜底模板` | app/services/ai_validator.py |
| 4 | 14 | `feat: 缓存服务 — 内存 LRU + SQLite 缓存` | app/services/cache_service.py |
| 4 | 15 | `feat: API — POST /game/start 创建游戏端点` | app/routers/game.py (partial) |
| 4 | 16 | `feat: API — POST /game/event + /choose 事件端点` | app/routers/game.py (partial) |
| 4 | 17 | `feat: API — GET /state + POST /end + GET /leaderboard` | app/routers/game.py (complete) |
| 5 | 18 | `feat: 28 个事件模板 YAML 数据 + 启动验证` | app/data/events/*.yaml |
| 5 | 19 | `feat: Prompt 模板 — System/User prompt 设计` | app/data/prompts/*.yaml |
| 5 | 20 | `test: 端到端集成测试 — 完整 60 事件游戏循环` | tests/test_e2e.py |
| 5 | 21 | `test: 边界 case + AI 降级测试` | tests/test_edge_cases.py |

---

## Success Criteria

### Verification Commands
```bash
uv run pytest                          # Expected: all pass, 0 failures
uv run pytest tests/test_e2e.py        # Expected: 60-event game completes
uv run pytest tests/test_edge_cases.py # Expected: all edge cases handled
uv run uvicorn app.main:app            # Expected: server starts on :8000
curl http://localhost:8000/docs         # Expected: Swagger UI loads
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] `uv run pytest` 全部通过
- [ ] 60 次事件 E2E 测试通过
- [ ] AI 降级场景测试通过（mock 500）
- [ ] 8 种结局均可触发
- [ ] 评分确定性验证（相同状态=相同分数）
- [ ] services/ 层零 FastAPI 导入
- [ ] 所有 API 响应符合 Pydantic schema
