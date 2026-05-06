# AGENTS.md — 修仙人生模拟器 (Random Story)

> 层次化知识库 · 自动生成 · 面向 AI Agent 导航

## 项目概览

修仙人生模拟器 — 一个 Web 端修仙题材文字冒险游戏。玩家选择天赋、分配属性、经历随机事件、修炼突破，追求飞升。

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
│       ├── events/             # 64+ YAML 事件模板
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
- 9级境界: 凡人→练气→筑基→金丹→元婴→化神→合体→大乘→渡劫飞升
- 用字统一: **"练气"** (非"炼气") — AI 输出纠正已在 SYSTEM_PROMPT
- 灵石: 凡人上限50, 练气1000, 按境界递增
- 事件模板 64+ YAML: 14大类 (daily/adventure/combat/social/economy/emotional/heavenly/fortune/sect/stones/explore/bottleneck/birth/childhood)
- 安静年机制: 连续2+事件后25%概率触发 narrative_only 无选项事件
- 突破: cultivation 溢出触发, 前端 waiting_click 模式等待玩家点击

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
