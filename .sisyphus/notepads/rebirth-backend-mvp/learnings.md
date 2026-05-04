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

# Task 4: 配置管理 — pydantic-settings + .env + 依赖注入

## 完成时间
2026-05-04

## 关键决策
- `Settings._env_file=None` 用于测试默认值场景，避免被工作目录下的 `.env` 文件干扰
- `get_config()` 使用 `@lru_cache` 实现单例模式，确保全应用共享同一个 Settings 实例
- `get_db()` 直接委托给 `app.database.get_db()`，保持一致的行为（row_factory、pragmas）
- `AIServiceProtocol` 定义为 `typing.Protocol`，在依赖中只定义接口不实现逻辑，后续由具体 AI service 实现
- `get_ai_service()` 返回 stub 占位实现，后续替换为真实 `OpenAIService`

## 注意事项
- pydantic-settings v2 使用 `SettingsConfigDict(env_file=".env")` 声明配置源
- `Settings` 构造函数支持 `_env_file` 参数动态指定 .env 路径，便于测试
- 环境变量优先级高于 .env 文件（pydantic-settings 默认行为）
- 不设置 `DEEPSEEK_API_KEY` 不会报错（字段类型为 `str = ""`）
- `issubclass(MyProtocol, typing.Protocol)` 在 Python 3.11+ 可以正确判断 Protocol 类型

## 文件清单
- `app/config.py` — Settings(BaseSettings) 从 .env 加载配置，含 7 个字段
- `app/dependencies.py` — AIServiceProtocol + get_config() + get_db() + get_ai_service()
- `tests/test_config.py` — 19 项测试全覆盖（默认值、环境变量覆盖、.env 文件加载、DI 函数）

# Task 5: 天赋卡系统 — 20张天赋卡YAML数据 + 抽卡逻辑服务

## 完成时间
2026-05-04

## 关键决策
- `draw_cards()` 使用两阶段抽卡算法：先按品级权重 `random.choices(weights=rarity)` 选品级，再从该品级均匀随机选卡
- 使用 `_talents_cache` 模块级缓存避免每次调用重复读 YAML
- `effects` 统一结构为 `{"attr_bonuses": {...}, "modifiers": {...}}`，双面卡额外有 `positive_effects`/`negative_effects`
- 双面卡(l06/x04/s03)同时保留 `effects: {}` 保证所有卡统一有 `effects` 字段
- 无需 Pydantic 模型，YAML 字典直接使用（简化，不需要序列化验证）
- `validate_selection()` 返回 `tuple[bool, str]` 而非抛出异常，便于上层使用

## 注意事项
- `tests/test_services/` 子目录需要 `__init__.py` 才能正确导入模块
- 抽卡 `random.seed()` 在不同品级数量下稳定可复现
- YAML rarity 值（0.4/0.3/0.2/0.08/0.02）放在每张卡上，两阶段算法会自动按品级权重分配
- 20000 次抽卡 × 3张 = 60000 样本量的分布测试全部通过（±3% tolerance）

## 文件清单
- `app/data/talents.yaml` — 20张天赋卡结构数据（凡品6/灵品6/玄品4/仙品3/神品1）
- `app/services/talent_service.py` — load_talents() + draw_cards() + validate_selection()
- `tests/test_services/__init__.py` — 测试包初始化
- `tests/test_services/test_talent.py` — 23 项测试全覆盖（数据验证 + 抽卡逻辑 + 概率分布）

# Task 6: 境界系统 — 9层境界YAML配置 + realm服务

## 完成时间
2026-05-04

## 关键决策
- 凡人/渡劫飞升的 `stages: null` 在 PyYAML 中解析为 Python None，通过 `if not stages` 统一处理
- `get_stage_name` 使用通用公式 `int(progress * len(stages))` 均匀分割进度，适用于练气9层和筑基4阶段
- `spirit_stone_cap`/`technique_slots` 按境界指数级增长：凡人0→大乘100万灵石/7格功法
- 渡劫飞升作为最高境界，`cultivation_req: null`，`can_breakthrough` 对 null req 返回 False
- YAML 中 `time_span: null` 使用 YAML 的 null 字面量，对应 Python None
- `get_next_realm("渡劫飞升")→None` 通过查找 order+1 实现，找不到时返回 None

## 境界数据
| 境界 | 寿元 | 时间跨度 | 子阶段 | 突破需求 |
|------|------|---------|--------|---------|
| 凡人 | 80 | 5年 | 无 | 0 |
| 练气 | 120 | 1年 | 9层 | 100 |
| 筑基 | 200 | 5年 | 初/中/后/圆满 | 300 |
| 金丹 | 500 | 10年 | 初/中/后/圆满 | 1000 |
| 元婴 | 1000 | 20年 | 初/中/后/圆满 | 3000 |
| 化神 | 3000 | 50年 | 初/中/后/圆满 | 10000 |
| 合体 | 8000 | 100年 | 初/中/后/圆满 | 30000 |
| 大乘 | 20000 | 200年 | 初/中/后/圆满 | 100000 |
| 渡劫飞升 | ∞ | ∞ | 无 | null（最高） |

## 文件清单
- `app/data/realms.yaml` — 9层境界配置数据
- `app/services/realm_service.py` — load_realms() + get_realm_config() + get_stage_name() + can_breakthrough() + get_next_realm()
- `tests/test_services/test_realm.py` — 30 项测试全覆盖（数据验证 + 子阶段映射 + 突破判断 + 境界链条）

# Task 7: 门派系统 — 3门派YAML + sect服务

## 完成时间
2026-05-04

## 关键决策
- `join_conditions` 使用结构化 YAML 表示（`logic: OR/AND/SINGLE/ALWAYS`），避免硬编码判断
- `check_join_conditions` 接收 camelCase 键名的 dict (`rootBone`, `comprehension`, `mindset`, `luck`)
- 万剑山庄使用 `logic: OR` 支持任一条满足即可
- 逍遥派使用 `logic: SINGLE`（只有一个条件）
- 金刚寺使用 `logic: AND` 要求全部满足
- 散修使用 `logic: ALWAYS` 无条件加入
- 在数据层（YAML）编码门派配置，业务逻辑保持通用

## 注意事项
- 门派加入为强制脚本事件(10-12岁触发)，校验逻辑在此实现，事件触发在其他任务中
- 散修的 `techniques: []` 为空列表，`weapon`/`attribute` 为 null
- 未实现隐秘传承/进阶功法/门派贡献/任务系统（超出范围）

## 文件清单
- `app/data/sects.yaml` — 4 个门派配置（万剑山庄、逍遥派、金刚寺、散修）
- `app/services/sect_service.py` — load_sects() + check_join_conditions() + get_sect_techniques()
- `tests/test_services/test_sect.py` — 25 项测试全覆盖（数据验证 + 4条加入路线 + 散修无条件 + 功法查询）

# Task 8: 事件引擎 — 事件加载 + 筛选 + 权值 + 随机选择

## 完成时间
2026-05-04

## 关键决策
- `load_templates()` 使用 `glob.glob("*.yaml")` 扫描 `app/data/events/` 目录，自动发现所有事件模板
- `_templates_cache` 模块级缓存，避免重复 I/O（与 talent_service、realm_service 一致）
- 境界比较使用 `_get_realm_order()` 获取 order 字段（1-based: 凡人=1, 渡劫飞升=9），通过 `get_realm_config()` 查询
- `calculate_weights()` 返回 `list[tuple[dict, float]]` 便于 `random.choices` 直接使用
- 瓶颈权重：`cultivation_req` 为 None 或 0 时权重=1.0（`"if req is None or req == 0"`），避免除零
- `select_event()` 空池返回硬编码 `FALLBACK_EVENT`，不抛异常
- `build_event_context()` 使用 `str.format()` 替换 `{realm}` 和 `{age}` 占位符
- 未知事件类型默认权重=1.0

## 注意事项
- 测试数据文件以 `_` 前缀命名（`_test_daily.yaml`、`_test_jindan.yaml`），便于区分测试数据和生产数据
- realm_service 的 `get_realm_config()` 返回 `dict` 或 `None`，需要判空处理
- `cultivation_req=0`（凡人）和 `cultivation_req=None`（渡劫飞升）统一处理为权重=1.0
- `random.choices` 的 `k=1` 返回 `list`，需要取 `[0]` 拿到元素
- `zip(*weighted_templates)` 解包会产生 `tuple`，需要用 `list()` 转换后传参

## 事件权重公式
| 事件类型 | 权重公式 | 说明 |
|---------|---------|------|
| daily | 1.0 | 默认基准权重 |
| adventure | 0.3 + luck × 0.05 | 气运越高，奇遇概率越大（0.3–0.8） |
| bottleneck | 0.5 + (cultivation/req) × 0.5 | 修为越接近突破门槛，瓶颈事件概率越大（0.5–1.0） |

## 文件清单
- `app/data/events/_test_daily.yaml` — 通用日常测试事件（全境界通用）
- `app/data/events/_test_jindan.yaml` — 金丹限定测试事件（境界/年龄过滤）
- `app/services/event_engine.py` — load_templates() + filter_templates() + calculate_weights() + select_event() + build_event_context() + should_force_non_daily()
- `tests/test_services/test_event_engine.py` — 24 项测试全覆盖

# Task 10: 评分系统 — 8结局判定 + 分数 + 等级

## 完成时间
2026-05-04

## 关键决策
- `determine_ending(player_state, age, ascended=False)` 签名比 spec 多 `age` 和 `ascended` 两个参数，因为 `PlayerState` 模型中没有这些字段（Task 3 已完成，不可修改）
- `calculate_score(player_state, ending, age, technique_grades)` 多 `age` 和 `technique_grades` 两个参数，因为 `PlayerState.techniques` 是 `list[str]`（技术 ID 列表），不含 grade 信息
- `technique_grades` 接受显式的品级字符串（如 `["灵品", "玄品"]`），让调用方（game_service）负责从 YAML/sect 数据中查找 grade
- 境界 order 使用 YAML 1-indexed 转 0-indexed：`(yaml_order - 1) / 8 * 50`，因为 YAML 配置中 order=1（凡人）至 order=9（渡劫飞升），而评分公式要求 0-indexed（凡人=0，渡劫飞升=8）
- `get_grade()` 使用阈值降序查找，先匹配最高分区间

## 注意事项
- `PlayerState.lifespan` 类型为 `int`，但 YAML 中渡劫飞升的 lifespan 为 `"无限"`（字符串）。game_service 在设置渡劫飞升玩家的 lifespan 时需要处理此转换（如使用很大的 int 值）
- 评分是纯算术，不需要 `random` 模块，也不调用 `random.seed()`
- 8 种结局全部定义在 `_ENDING_BONUS` 映射中，但 MVP 只触发 3 种（飞升成仙/功德圆满/寿终正寝），其余 5 种有默认 bonus=0.3
- 境界分最大 50 分（渡劫飞升），寿命分最大 20 分（完全活满），功法分最大 20 分（仙品功法），结局分最大 10 分（飞升成仙）
- `_get_realm_order()` 使用 `get_realm_config()` 查询，unknown realm 返回 0
- `_has_infinite_lifespan(realm)` 检查 YAML 中该境界的 lifespan 是否为字符串 `"无限"`，用于：1) `determine_ending` 中阻止触发寿终/功德圆满（无限寿命无法自然死亡）；2) `calculate_score` 中给寿命分满分 20
- 即使 `PlayerState.lifespan` 存为 int 无法直接表示 `"无限"`，通过 `_has_infinite_lifespan()` 检查 realm YAML 配置来正确识别渡劫飞升的无限寿命状态
- `test_breakthrough.py` 引用了未实现的 `app.services.breakthrough`，执行 `pytest -q` 时会报错（不影响其他测试，是预留给 Task N 的占位文件）

## 文件清单
- `app/services/scoring.py` — determine_ending() + calculate_score() + get_grade() + _has_infinite_lifespan()
- `tests/test_services/test_scoring.py` — 49 项测试全覆盖（结局判定 ×8 + 评分确定性 + 4 维度组件 + 等级映射 ×21 参数化 + 渡劫飞升无限寿命 ×2）

# Task 9: 突破系统 — 成功率计算 + 境界升降 + 百折不挠天赋

## 完成时间
2026-05-04

## 关键决策
- `attempt_breakthrough()` 接收 `player_state: dict` 而非 Pydantic 模型，便于 service 层灵活调用
- `calculate_success_rate()` 公式：0.50 + rootBone×0.05 + comprehension×0.03 + mindset×0.02 - realm_penalty + pill_bonus(0.15)，上下限 0.05-0.95
- 成功 → 境界提升（get_next_realm），cultivation 归零；`渡劫飞升` 作为目标境界，成功标志 `ascended=True`
- 失败 → cultivation 损失 20-50%（random.uniform），10% 概率境界跌落（_get_prev_realm）
- 百折不挠（id=f06）通过名称匹配而非硬编码 ID：`_has_talent()` 从 `load_talents()` 构建 name→id 映射，查 player_state 的 talent_ids
- 百折不挠效果：失败时 loss_ratio 减免 0.10（不低于 0）
- 已在渡劫飞升的玩家：直接返回 `success=True, ascended=True`，不修改任何属性
- `BreakthroughResult` 为 `@dataclass`，5 个字段：success, new_realm, cultivation_loss, realm_dropped, ascended

## 注意事项
- `get_realm_penalty()` 从 REALM_PENALTY 字典查找，未知境界返回 0.0
- 成功时不调用 `random.uniform`（loss_ratio），避免浪费随机序列
- 境界跌落从 `_get_prev_realm()` 通过 `order-1` 查找，凡人（order=1）返回 None — 不会跌落到非法境界
- 测试使用 `pytest.approx(0.15)` 处理浮点精度（0.50 - 0.35 = 0.15000000000000002）
- 测试用 `random.seed()` 固定随机性，关键 seed：seed=1（凡人成功→练气），seed=22（练气失败+跌落），seed=2（凡人失败但无跌落 + cultivation_loss 验证）

## 文件清单
- `app/services/breakthrough.py` — BreakthroughResult + get_realm_penalty() + calculate_success_rate() + attempt_breakthrough()
- `tests/test_services/test_breakthrough.py` — 32 项测试全覆盖（惩罚 ×9 + 成功率 ×12 + 成功路径 ×2 + 失败路径 ×5 + 天赋效果 ×2 + 边界条件 ×2）

# Task 11: 游戏服务 — 生命周期 + 状态推进 + 修为公式

## 完成时间
2026-05-04

## 关键决策
- 状态存储使用模块级 `_games: dict[str, dict]` dict（MVP 不做数据库集成，T15-T17 负责）
- session_id 使用 `uuid.uuid4().hex[:16]` 生成 16 字符 Hex 字符串
- player_state 使用 dict 而非 Pydantic PlayerState（game_service 内部使用 dict，仅在 end_game 结算时构建 PlayerState 传给 scoring）
- 与 event_engine 的接口适配：game_service 维护嵌套 attributes dict（`{"rootBone": ..., "comprehension": ..., "mindset": ..., "luck": ...}`），但 event_engine 的 `calculate_weights` 和 `filter_templates` 期望扁平结构（顶层 `luck`/`realm`/`age`/`faction`/`cultivation`）。通过 `_to_engine_context()` 辅助函数将玩家状态扁平化为 event_engine 需要的格式
- `_current_event` 存储在玩家状态中（get_next_event 写入，process_choice 读取后删除），存储 `{id, type, title, options}`
- `get_next_event` 不调用 AI，只调用 event_engine 选择模板并构建上下文（AI 调用在上层 API）
- `process_choice` 不调用 AI，只处理数值结算

## 修为公式
```
cultivation_gain = base × (1 + comprehension × 0.1) × technique_modifier
```
- base 按事件类型: daily=10, adventure=30, bottleneck=5
- technique_modifier: 无功法=0.5, 凡品=1.0, 灵品=1.5, 玄品=2.0, 仙品=3.0
- 多功法取平均: `sum(mods) / len(mods)`

## 修为溢出处理
- 当 cultivation >= next_realm.cultivation_req 时触发溢出
- 凡人→练气: 100 为阈值（练气的 cultivation_req），超出部分带入 realm_progress
- realm_progress = overflow / next_realm_cultivation_req
- 渡劫飞升（最高境界）get_next_realm 返回 None，跳过溢出处理

## 游戏结束条件（check_game_over）
- age >= lifespan → True
- event_count >= 60 → True
- ascended == True → True
- 否则 False

## 注意事项
- 凡人 spirit_stone_cap=0，测试灵石增加时需要切换到 练气（cap=1000）
- end_game 时构建 PlayerState 对象传给 scoring 函数（determine_ending、calculate_score），因为 scoring 接受 Pydantic 模型而非 dict
- end_game 不修改 scoring 的实现（不修改已有服务）
- process_choice 中 `del state["_current_event"]` 防止后续误用
- 属性校验复用 `talent_service.validate_selection()`，不重复实现
- 性别校验用 `in ("男", "女")`，与 Pydantic Literal 约束一致

## 文件清单
- `app/services/game_service.py` — start_game + get_next_event + process_choice + get_state + end_game + check_game_over + _calc_cultivation_gain
- `tests/test_services/test_game_service.py` — 43 项测试全覆盖

# Task 17: API 端点 GET /state + POST /end + GET /leaderboard

## 完成时间
2026-05-04

## 关键决策
- 创建 `app/routers/game.py` 作为游戏 API 路由器，prefix=`/api/v1/game`
- `get_state` 端点不指定 `response_model`，因为 in-memory dict 结构与 `PlayerState` Pydantic 模型（扁平 snake_case）不一致（in-memory 使用嵌套 camelCase attributes dict）
- `end_game` 端点不指定 `response_model`，因为 `GameEndResponse` 现有模型定义（`final_state`+`reason`）与 `end_game()` 服务返回（`ending`+`score`+`grade`）不匹配；直接返回 dict 避免破坏已有模型测试
- 新增 `EndGameRequest` 模型（仅 `session_id` 字段），因为 `EventRequest` 现有模型使用 `player_id` 而非 `session_id`
- 使用 `try/except ValueError` 处理 `get_state()` 和 `end_game()` 的 session 不存在情况，转换为 404 HTTP 响应
- 注册 router 到 `app/main.py` 使用 `app.include_router(game.router)`

## 注意事项
- `game_service.get_state()` 在 session 不存在时 raise `ValueError`（不返回 None），需要在端点中 try/except
- `game_service.end_game()` 同样 raise `ValueError`，但 spec 中检查 `result is None` 作为冗余保护
- 测试用 `httpx.AsyncClient(transport=ASGITransport(app=app))` 而非 TestClient，避免同步包装
- `tests/test_api/__init__.py` 需要创建（空文件），否则 pytest 不会发现包内测试
- `LeaderboardEntry` 模型在 Task 3 中已预定义，MVP 返回空列表即可

## 文件清单
- `app/models/game.py` — 新增 `EndGameRequest` 模型
- `app/routers/game.py` — 3 个端点（state、end、leaderboard）
- `app/main.py` — 注册 `game` router
- `tests/test_api/__init__.py` — 测试包初始化
- `tests/test_api/test_game_endpoints.py` — 5 项 API 测试

# Task 12: AI 服务 — DeepSeek API 封装 + JSON 模式 + 重试

## 完成时间
2026-05-04

## 关键决策
- `DeepSeekService` 直接使用 `openai.OpenAI` client（DeepSeek API 兼容 OpenAI SDK），通过 `response_format={"type": "json_object"}` 强制 JSON 模式
- Settings 字段名使用大写（`DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, `DEEPSEEK_BASE_URL`），与 config.py 中 pydantic Settings 定义一致
- 重试逻辑：`_max_retries = 2`（共 3 次尝试），指数退避 `2^attempt + 1`（1s, 3s），空 content 重试间隔固定 1s
- 三类异常处理：`APIError/APIConnectionError`（重试）→ `json.JSONDecodeError`（立即 fallback）→ 全部重试失败（fallback 空结果）
- `MockAIService` 含 `call_count` 追踪，便于上层测试验证 AI 被调用次数
- 不修改 `app/dependencies.py`（任务约束），Protocol 合规通过 `hasattr + callable` 检查

## 注意事项
- `AIServiceProtocol` 在 dependencies.py 中没有 `@runtime_checkable` 装饰器，不能用 `isinstance()` 做 Protocol 检查，会抛 `TypeError`
- 测试 mock `app.services.ai_service.OpenAI`（模块路径），不是 `openai.OpenAI`（包路径），否则 mock 不生效
- `APIError` 构造需要 `request` 和 `body` 参数，测试中用 `MagicMock()` 填充
- DeepSeek 空 content 已知问题：偶发返回 `content=""` 或 `content=None`，重试可恢复
- fallback 结果结构为 `{"narrative": "", "options": []}`，上层服务需要处理空 narrative

## 文件清单
- `app/services/ai_service.py` — DeepSeekService + MockAIService
- `tests/test_services/test_ai_service.py` — 9 项测试（Mock ×3 + 重试 ×2 + JSON 解析 ×2 + Protocol ×2）

# Task 15: API 端点 — POST /game/start 创建游戏

## 完成时间
2026-05-04

## 关键决策
- `GameStartRequest.attributes` 使用 Pydantic `Attributes` 模型（snake_case），`start_game()` 服务层期望 camelCase keys（`rootBone`/`comprehension`/`mindset`/`luck`），router 中手动转换 bridge
- `GameStartResponse.state` 类型为 `PlayerState`（非 `initial_state`），需要将 `start_game()` 返回的 dict 中嵌套的 `attributes` dict 展平为 `PlayerState` 的扁平字段
- 不需要新建模型或修改现有模型，现有 `GameStartRequest`/`GameStartResponse`/`PlayerState` 完全满足需求
- `GameStartResponse(state=PlayerState(...))` 构造时，`PlayerState` 中 `start_game` dict 未提供的字段（`health`/`qi`/`score`/`ending_id`/`last_active_at`/`created_at`/`updated_at`）使用默认值

## 注意事项
- `app/routers/game.py` 已在 Task 17 中创建（GET /state + POST /end + GET /leaderboard），只需在同一个 `router` 对象上添加 `@router.post("/start")` 装饰器
- `app/main.py` 已包含 `app.include_router(game.router)`，不需要额外注册
- Pydantic 验证优先于服务层验证：`Attributes.validate_sum()` 在请求进入 handler 前就返回 422，`start_game()` 内部的 `if total != 10` 是冗余校验
- 测试使用 `httpx.AsyncClient(transport=ASGITransport(app=app))`，与 Task 17 的测试风格一致

## 文件变更
- `app/routers/game.py` — 新增 `POST /start` 端点（同时保留现有 GET /state, POST /end, GET /leaderboard）
- `tests/test_api/test_game_start.py` — 5 项 API 测试（成功创建 ×1 + 无效属性总和 ×1 + 无效性别 ×1 + 无效天赋卡ID ×1 + 缺少必填字段 ×1）

# Task 14: 缓存服务 — 内存 LRU + SQLite 双层缓存

## 完成时间
2026-05-04

## 关键决策
- 双层缓存架构：内存 LRU (`OrderedDict`) 作为 L1，SQLite (`ai_cache` 表) 作为 L2，兼顾速度和持久性
- 缓存 key 格式：`template_id:realm:category`，定界符用冒号 (`:`)，避免与字段内容冲突
- LRU 淘汰策略：`OrderedDict.move_to_end()` + `popitem(last=False)`，O(1) 复杂度
- TTL 为 30 分钟（1800 秒），内存和 SQLite 共享相同 TTL 判定逻辑
- SQLite 的 `created_at` 显式存为 Unix 时间戳字符串（`str(time.time())`），避免 SQLite 默认 TIMESTAMP 格式（`YYYY-MM-DD HH:MM:SS`）的浮点数转换问题
- `hit_count` 字段暂不更新（超出范围，仅保留 schema 中已有的列定义）
- `get_cached()` 的 `category` 参数默认为空字符串，`set_cached()` 要求显式提供（调用方必须确认分类）
- SQLite 回填内存缓存：当内存未命中但 SQLite 命中时，自动将结果写回 LRU 缓存，后续查询直接走内存

## 注意事项
- `sqlite3.Row` 不是 `dict` 的子类，`isinstance(row, dict)` 返回 False，需要用索引访问或显式判断 `sqlite3.Row`
- 测试 SQLite 时需要用内存数据库 (`:memory:`) + 手动创建 `ai_cache` 表，不依赖 `init_db()`
- TTL 测试通过 `mock time.time` 实现，比 `time.sleep` 快且可靠
- LRU 测试需要 `clear_cache()` 保证隔离，否则 101 条写入可能因前序测试残留数据导致误判
- `INSERT OR REPLACE` 依赖 `cache_key` 的 UNIQUE 约束实现幂等更新
- `db.execute()` 返回的 `Cursor` 不自动提交，需要显式 `db.commit()`
- 异常处理使用 `except Exception: pass` 包裹所有 SQLite 操作，确保 SQLite 故障不会影响主流程

## 文件清单
- `app/services/cache_service.py` — get_cached() + set_cached() + clear_cache() + _make_key()
- `tests/test_services/test_cache_service.py` — 7 项测试（miss + hit + TTL过期 + LRU淘汰 + SQLite回填 + key格式 ×2）
