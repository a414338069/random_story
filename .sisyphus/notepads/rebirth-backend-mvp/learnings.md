# Task 1: 项目骨架 + pyproject.toml + uv 配置

## 完成时间
2026-05-04

## 关键决策
- 使用 `uv init --python 3.11` 初始化项目，Python 3.11+ 兼容
- `uvicorn[standard]` 而非 `uvicorn`，以获得 watchfiles/uvloop 等性能增强
- CORS 允许所有来源 (`*`)，MVP 阶段不限制

## 依赖版本记录
- fastapi==0.136.1
- pydantic==2.13.3
- pydantic-settings==2.14.0
- openai==2.33.0
- pyyaml==6.0.3
- uvicorn==0.46.0
- pytest==9.0.3
- httpx==0.28.1
- pytest-asyncio==1.3.0

## 注意事项
- uv init 会创建 README.md，保留即可
- pytest.ini 不需要额外配置，pyproject.toml 自动发现测试
- pytest-asyncio 1.3.0 使用 strict 模式，注意 fixtrue scope
- 使用 `app.main` 模块路径而非 `rebirth_backend`（uv init 创建的脚本入口不适用）

## 目录结构
```
app/
├── __init__.py
├── main.py              # FastAPI app + CORS + /health
├── models/              # Pydantic schemas (Task 3)
├── routers/             # API endpoints (Task 15-17)
├── services/            # Business logic (Task 5-14)
└── data/
    ├── prompts/         # AI prompt templates (Task 19)
    └── events/          # Event YAML templates (Task 18)
tests/
├── __init__.py
└── test_health.py       # 健康检查 (TDD: GREEN)
```

## 2026-05-04: Removing uv init default files

- `uv init` generates a `src/<package_name>/` layout, but this project uses `app/` layout
- After deleting `src/`, `uv_build` fails because it expects `src/rebirth_backend/__init__.py`
- Solution: set `[tool.uv] package = false` — tells uv this is a virtual project (no package to build)
- The `uv run` command still works correctly by adding the project root to PYTHONPATH, allowing `from app.main import app` imports to resolve
- Deleting `[project.scripts]` section is safe since the project doesn't expose a CLI entry point (it's a FastAPI server started via `uvicorn`)

# Task 2: 数据库层 — schema.sql + 连接工厂 + init_db

## 完成时间
2026-05-04

## 关键决策
- 使用同步 `sqlite3`（非 aiosqlite/ORM），Schema 和数据库层分离
- `get_db()` 设置 `row_factory = sqlite3.Row`，支持列名访问
- `get_db()` 设置 `PRAGMA foreign_keys=ON` 和 `PRAGMA journal_mode=WAL`
- `init_db()` 使用 `CREATE TABLE IF NOT EXISTS` 实现幂等性
- `app/main.py` 使用 FastAPI `lifespan` 上下文管理器启动时自动建表
- 测试使用 `:memory:` 内存数据库隔离
- schema.sql 放到项目根目录，`app/database.py` 通过相对路径 `../schema.sql` 引用

## 注意事项
- SQLite 的 `AUTOINCREMENT` 会隐式创建 `sqlite_sequence` 内部表，查询表列表时需过滤 `name NOT LIKE 'sqlite_%'`
- `executescript()` 隐式包含 BEGIN/COMMIT，不需要额外调用 `db.commit()`
- `PRAGMA foreign_keys=ON` 是连接级别的设置，需要在每个连接上单独启用
- sqlite3 中 BOOLEAN 存为 INTEGER (0/1)

## 文件清单
- `schema.sql` — 4 张表 DDL（players, event_logs, ai_cache, event_templates）
- `app/database.py` — get_db() 连接工厂 + init_db() 自动建表
- `tests/test_database.py` — 16 项测试（建表验证 + 各表 Schema + CRUD + UNIQUE/FK 约束）

# Task 3: Pydantic 数据模型 — 创建所有 API 请求/响应的 Pydantic v2 schemas

## 完成时间
2026-05-04

## 关键决策
- `Attributes` 使用 `model_validator(mode='after')` 校验四项属性总和==10，放在 Attributes 自身而非 GameStartRequest，自然保护所有引用它的模型
- `EventResponse.narrative` 使用 `field_validator` 校验 20-500 字（强业务约束，用 validator 比 Field 更语义清晰）
- `EventResponse.options` 同时使用 `Field(min_length=2, max_length=3)` + `field_validator` 双重校验
- `PlayerState` 映射 players 表所有字段，`is_alive` 用 bool（Pydantic v2 自动处理 bool↔int 转换）
- `talent_ids`/`techniques`/`inventory` 在模型中为 `list[str]`，DB 存储 JSON TEXT，转换在 service 层处理
- `GameStartRequest.talent_card_ids` 用 `Field(min_length=3, max_length=3)` 确保精确 3 张天赋卡
- `gender` 使用 `Literal["男","女"]` 编译期约束

## 注意事项
- `Attributes` 不支持无参构造（默认 sum=0≠10），必须在创建时提供有效的属性分配
- 中文字符计数用 Python 的 `len()` 即可（每个中文字算 1 个字符）
- Pydantic v2 的 `model_dump()` 和 `model_validate()` 支持 JSON 序列化/反序列化 round-trip
- `Optional[str] = None` 在不传时序列化为 `null`，符合 JSON 规范
- 字段注解类型的顺序很重要：`Optional[str]` 与有默认值的 `Field()` 配合时，类型注解中没有 `= None` 会导致 JSON schema 中 type 错误；使用 `Optional[str] = None` 或 `str = Field(default=None)` 均可

## 文件清单
- `app/models/player.py` — Attributes, Technique, InventoryItem, SectInfo, PlayerState
- `app/models/event.py` — EventOption, EventResponse, EventRequest, EventChooseRequest
- `app/models/game.py` — GameStartRequest, GameStartResponse, GameEndResponse, LeaderboardEntry
- `tests/test_models.py` — 38 项测试全覆盖
