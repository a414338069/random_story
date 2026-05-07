# AGENTS.md — 修仙人生模拟器 (Random Story)

> 层次化知识库 · 自动生成 · 面向 AI Agent 导航

---

## Game Overview — 这是什么游戏

### 一句话概括
> **AI驱动的修仙题材文字冒险游戏。** 没有战斗动画、没有地图探索——你的人生就是你的游戏。你选择天赋、分配属性，AI 为你生成独一无二的修仙人生叙事。每次选择都有后果，每次突破都攸关生死。

---

### 玩家旅程（从开局到结算）

```
创建角色 ──→ 天赋抽卡 ──→ 分配属性 ──→ 进入主循环
                                          ↓
                                ┌──── 获取事件(文字叙事)
                                │         ↓
                                │     有选项? ──→ 是 → 选择 → 计算后果
                                │         ↓                    ↓
                                │        否 → 安静年(叙事only)  ↓
                                │                               ↓
                                │                    ┌─── 突破条件满足?
                                │                    ↓         ↓
                                │                    是 → 突破事件(选择丹药/硬冲)
                                │                    ↓    success=新境界/fail=惩罚
                                │                    ↓
                                └──────── 循环直到死亡|飞升
                                                ↓
                                            结算评分
```

- **每局都是独立人生**：天赋随机抽卡 + 属性自选 + AI 生成事件 = 几乎不重复
- **目标**：从凡人修炼到渡劫飞升，途中避免死亡（寿尽/走火入魔/意外）
- **结算**：按最终境界 + 成就评分，评级 F → SSS

---

### 核心玩法

| 机制 | 说明 |
|------|------|
| **境界** | 9级：凡人→炼气→筑基→金丹→元婴→化神→合体→大乘→渡劫飞升。境界越高寿命越长、上限越高 |
| **修炼** | 每次事件选择产出 `cultivation_gain`，积累到阈值后触发突破事件 |
| **突破** | **高风险高回报**：突破成功=升境界+加属性；失败=修为归零/受伤/折寿。可用丹药提高成功率 |
| **天赋** | 开局抽卡选3张，影响突破概率、修炼速度、事件权重等。0.5%出绝世天赋 |
| **属性** | 4维可分配（根骨/悟性/心境/福缘），各影响不同方面（修炼/收益/概率/事件质量） |
| **灵石** | 货币，在事件中获取和使用，境界越高存储上限越高 |
| **生命阶段** | INFANT(0-3)→CHILD(4-11)→YOUTH(12-15)→CULTIVATOR(16+)。儿童期不修炼，青年期减半 |
| **寿元** | 每过一年-1，突破增加寿元，寿尽即死。最终目标是飞升前不死 |

### 这不是什么

- ❌ 不是 MMORPG — 单机文字游戏
- ❌ 不是挂机游戏 — 需要做选择
- ❌ 不是视觉小说 — AI 动态生成，非固定剧本
- ❌ 没有战斗系统 — 事件驱动，非战力数值

---

### AI 驱动叙事（核心卖点）

```
1. event_engine 从 76 个 YAML 模板中筛选符合条件的模板
2. 命中模板池后，模板的 {prompt_template} + 玩家状态 → AI prompt
3. DeepSeek API 生成：{narrative, options[{id, text, consequences}], ...}
4. ai_validator 3 层验证：JSON解析 → Schema校验 → 业务规则
5. 前端展示：打字机效果慢慢显示文字，玩家阅读后选择
6. 选择后果由 AI 计算的 consequences 决定（非预设事件树）
```

**关键**：AI 不写剧本——它根据模板框架 + 玩家状态，**即兴创作**每段叙事的细节。同样的"比武切磋"模板，凡人打街头架，金丹高手神通对决——现在甚至按境界分层级叙事。

---

### 难度 & 策略

- 总体难度偏硬核：突破失败惩罚严厉，寿元有限
- 策略点：
  - 什么时候冲突破（修为积攒 vs 成功率焦虑）
  - 吃不吃丹药（消耗灵石，但提高成功率）
  - 4维属性如何分配（没有完美方案，各有取舍）
  - 天赋组合（有些相克，有些配合）
- **没有"最优解"** — AI 生成事件的多样性让每个档的体验不同

---

## 项目结构

| 维度 | 技术 |
|------|------|
| 后端 | **FastAPI** + Python ≥3.11 + SQLite + uv 包管理 |
| 前端 | **Vue 3** + NaiveUI + TypeScript + Vite |
| AI | **DeepSeek API** (`deepseek-chat` / v4-flash) 生成叙事和选项 |
| 测试 | pytest 9.0 + pytest-asyncio (后端) / Vitest 4.x + Playwright (前端) |

## 目录结构

```
random_story/
├── app/                        # 后端 (FastAPI)
│   ├── main.py                 # 入口: FastAPI app + lifespan + CORS
│   ├── config.py               # Settings (pydantic-settings, 读 .env)
│   ├── database.py             # SQLite 连接 + init_db
│   ├── dependencies.py         # DI stubs (未使用)
│   ├── models/                 # Pydantic 模型 (request/response)
│   │   ├── game.py             # GameStartRequest/Response, EndGameRequest, LeaderboardEntry
│   │   ├── player.py           # PlayerState (核心玩家状态)
│   │   └── event.py            # EventRequest, ChooseRequest, ChooseResponse, BreakthroughInfo
│   ├── repositories/
│   │   └── game_repo.py        # SQLite CRUD (games, events, scores)
│   ├── routers/
│   │   └── game.py             # /api/v1/game/* (6 endpoints)
│   ├── services/               # → 见 app/services/AGENTS.md
│   │   ├── game_service.py     # 核心编排 (630行)
│   │   ├── event_engine.py     # 事件引擎 (模板加载+筛选+权重)
│   │   ├── ai_service.py       # DeepSeek + MockAIService
│   │   ├── ai_validator.py     # 3层AI输出验证
│   │   ├── breakthrough.py     # 突破系统
│   │   ├── cache_service.py    # LRU+SQLite双层缓存
│   │   ├── realm_service.py    # 境界系统
│   │   ├── scoring.py          # 评分+评级
│   │   ├── sect_service.py     # 门派系统
│   │   └── talent_service.py   # 天赋系统
│   └── data/                   # → 见 app/data/events/AGENTS.md
│       ├── realms.yaml         # 9级境界配置
│       ├── sects.yaml          # 门派配置
│       ├── talents.yaml        # 天赋配置
│       ├── events/             # 76 YAML 事件模板
│       ├── prompts/            # system.yaml + user.yaml
│       └── validate_data.py    # 数据校验 CLI
├── web/                        # 前端 (Vue 3)
│   └── src/                    # → 见 web/src/AGENTS.md
│       ├── main.ts             # 入口
│       ├── App.vue             # 根组件
│       ├── router.ts           # Vue Router
│       ├── api/                # API 客户端
│       ├── composables/        # Vue 组合式函数
│       ├── components/         # UI 组件
│       ├── views/              # 页面视图
│       ├── core/               # 类型 + 工具函数
│       ├── data/               # 前端静态数据
│       └── styles/             # CSS 主题 + 动画
├── tests/                      # 后端测试 (18文件)
│   ├── test_services/          # 服务单元测试 (9文件)
│   ├── test_api/               # API 集成测试 (3文件)
│   ├── test_data/              # 数据层测试 (2文件)
│   ├── test_e2e.py             # 全生命周期 E2E
│   └── test_edge_cases.py      # 边界条件
├── pyproject.toml              # Python 项目配置 (uv)
├── schema.sql                  # DB schema (参考)
├── .env                        # 环境变量 (不入库)
└── .env.example                # 环境变量模板
```

## 核心数据流

```
玩家操作 → Vue组件 → api/client.ts → FastAPI router
    → game_service (编排) → event_engine (选事件)
    → ai_service (生成叙事) → ai_validator (验证)
    → game_repo (持久化) → SQLite
    → 返回 JSON → Vue响应式更新
```

## API 端点

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/v1/game/start` | 创建游戏 (name, gender, talents, attributes) |
| GET | `/api/v1/game/state/{id}` | 查询当前状态 |
| POST | `/api/v1/game/event` | 获取下一个事件 |
| POST | `/api/v1/game/event/choose` | 处理玩家选择 |
| POST | `/api/v1/game/end` | 结算游戏 |
| GET | `/api/v1/game/leaderboard` | 排行榜 |

## 关键约束

### 技术约束
- Python ≥3.11 (使用 `X \| Y` 类型语法)
- 无 eslint/prettier/ruff/black/mypy 配置
- 无 conftest.py — 每个测试文件独立定义 fixture
- 无覆盖率工具配置
- SQLite 单文件数据库 (`app/data/rebirth.db`)
- DATABASE_PATH: `.env` 中 `data/game.db` vs `config.py` 默认 `app/data/rebirth.db` (不一致)

### 游戏规则
- 9级境界: 凡人→炼气→筑基→金丹→元婴→化神→合体→大乘→渡劫飞升
- 用字统一: **"炼气"** (非"练气") — AI 输出纠正已在 SYSTEM_PROMPT
- 灵石: 凡人上限50, 炼气1000, 按境界递增
- 事件模板 76 YAML: 16大类 (daily/adventure/combat/social/economy/emotional/heavenly/fortune/sect/stones/explore/bottleneck/birth/childhood/youth)
- 生命阶段: INFANT(0-3) / CHILD(4-11) / YOUTH(12-15) / CULTIVATOR(16+), 修炼乘数 0.0/0.0/0.5/1.0
- 安静年机制: 连续2+有选项事件后25%概率触发 narrative_only 无选项事件, 不受生命阶段影响
- 突破: 独立交互事件 (build_breakthrough_event), 含 use_pill/direct 两选项, 前端 breakthrough_choosing 阶段

### 已知技术债
- `dependencies.py`: `_StubAIService` 死代码 (从未被调用)
- `as any`: `AttributeAllocator.vue` 3处 + `TalentSelect.vue` 1处
- `except Exception: pass`: 8处静默吞异常 (无日志)
- CORS `allow_origins=["*"]`: 开发环境可接受, 生产需锁定

## 开发命令

```bash
# 后端
uv run uvicorn app.main:app --reload --port 8000
uv run pytest                    # 54 测试
uv run pytest tests/test_services/test_game_service.py -v  # 单文件

# 前端
cd web && npm run dev            # http://localhost:5173
cd web && npx vue-tsc --noEmit   # 类型检查
cd web && npm run test:unit      # Vitest 单元测试
cd web && npm run test:e2e       # Playwright E2E

# 数据校验
uv run python -m app.data.validate_data
```

## 子目录知识库

- [`app/services/AGENTS.md`](app/services/AGENTS.md) — 服务层详解
- [`app/data/events/AGENTS.md`](app/data/events/AGENTS.md) — 事件模板系统
- [`web/src/AGENTS.md`](web/src/AGENTS.md) — 前端架构
