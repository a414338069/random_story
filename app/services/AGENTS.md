# AGENTS.md — 服务层 (app/services/)

> 层次化知识库 · 自动生成 · 面向 AI Agent 导航

## 概览

服务层包含 11 个模块，是游戏的核心业务逻辑。`game_service.py` 是唯一编排层，其余 10 个是独立的领域服务。

## 文件清单

| 文件 | 行数 | 职责 | 依赖 |
|------|------|------|------|
| `game_service.py` | 629 | **核心编排** — 游戏生命周期、状态推进、修炼公式 | 全部服务 + repo |
| `life_stage.py` | 37 | **生命阶段** — 4阶段划分(INFANT/CHILD/YOUTH/CULTIVATOR), 修炼乘数, 突破限制 | (无外部依赖) |
| `event_engine.py` | 195 | **事件引擎** — YAML模板加载、条件筛选、权重计算、安静年 | realm_service |
| `ai_service.py` | 167 | **AI服务** — DeepSeek API封装、JSON模式、重试逻辑、SYSTEM_PROMPT | openai SDK, config |
| `ai_validator.py` | ~100 | **AI输出验证** — 3层验证(JSON→Schema→业务) | (无外部依赖) |
| `breakthrough.py` | 126 | **突破系统** — 概率计算、掉落惩罚、天赋加成 | realm_service, talent_service |
| `cache_service.py` | 85 | **双层缓存** — LRU内存 + SQLite持久化 | (无外部依赖) |
| `realm_service.py` | 66 | **境界系统** — YAML加载、境界查询、进阶判断 | realms.yaml |
| `scoring.py` | 129 | **评分系统** — 结局判定、分数计算、评级映射(纯函数) | realm_service |
| `sect_service.py` | 112 | **门派系统** — YAML加载、门派分配、门派效果 | sects.yaml |
| `talent_service.py` | 92 | **天赋系统** — YAML加载、抽卡、天赋验证、效果应用 | talents.yaml |

## 核心编排流 (game_service.py)

### 公开函数 (被 router 调用)

```
start_game(name, gender, talent_card_ids, attributes) → dict
get_state(session_id) → dict
get_next_event(session_id) → dict
process_choice(session_id, option_id) → dict
check_game_over(player_state) → bool
end_game(session_id) → dict
```

### 关键内部函数

| 函数 | 职责 |
|------|------|
| `_get_ai_service(settings)` | 创建 DeepSeekService 或 MockAIService (取决于 config) |
| `_build_ai_prompt(event_ctx, state)` | 构建AI提示词(玩家状态+事件上下文+最近摘要) |
| `_build_consequence_narrative(chosen_text, cultivation_gain, ...)` | 后果叙事生成(CONSEQUENCE_TEMPLATES模板系统) |
| `_calc_cultivation_gain(event_type, comprehension, technique_grades)` | 修炼收益计算(事件类型×悟性×功法品质) |
| `_check_breakthrough_warning(state)` | 突破前预警(cultivation ≥ 80%下一境界需求) |
| `_ensure_pending_breakthrough(state, player_state)` | 创建突破事件上下文(独立交互事件) |
| `build_breakthrough_event(state, player_state)` | 构建突破事件响应(含 use_pill/direct 两选项) |
| `handle_breakthrough_choice(state, player_state, option_id)` | 处理突破选择(调用 breakthrough.attempt_breakthrough) |
| `_to_engine_context(state)` | PlayerState → event_engine 上下文转换 |

### CONSEQUENCE_TEMPLATES (行 272-295)

后果叙事模板系统，按修炼变化方向分类：
- 大幅增长: 修炼有如神助，突破瓶颈
- 中度增长: 功力精进
- 小幅增长: 稍有感悟
- 零增长: 忙于俗务
- 小幅下降: 旧伤复发
- 大幅下降: 走火入魔

### 状态管理

- `_games: dict[str, dict]` — 内存游戏会话字典 (session_id → state dict)
- 无 Redis/外部状态 — 游戏状态同时持久化到 SQLite (game_repo)

## 事件引擎 (event_engine.py)

### 事件选择流程

```
load_templates() → filter_templates(player_state) → calculate_weights(templates, player_state)
    → select_event(weighted_templates, player_state)
    → build_event_context(template, player_state)
```

### 安静年机制

`select_event()` 内部实现：
1. 检查 `_consecutive_events` (通过 game_service 追踪)
2. 连续 ≥2 个有选项事件后，25% 概率触发安静年
3. 安静年: `_build_quiet_year_event(player_state)` — 随机选择叙事模板，无选项

### 权重因子

`calculate_weights()` 考虑：
- 基础权重 (YAML `weight` 字段)
- 运气修正 (player `luck` 属性)
- 修炼进度修正
- 境界匹配修正
- `should_force_non_daily()` — 连续daily过多时强制非daily事件

## AI 服务 (ai_service.py)

### 双实现

| 类 | 用途 | 触发条件 |
|----|------|---------|
| `DeepSeekService` | 生产环境 | `DEEPSEEK_API_KEY` 非空 |
| `MockAIService` | 测试/开发 | API key 为空或测试时 mock |

### SYSTEM_PROMPT (行 16-80)

包含：
- 角色设定(修仙世界叙事生成器)
- JSON schema (narrative + options + consequences)
- consequences 字段: `spirit_stones_gain`(-100~100), `cultivation_gain`(0~200)
- **"炼气" 非 "练气"** 纠正指令（已修正：现在统一使用"炼气"）
- 叙事风格指南(不要过于简短, 不要使用"你决定"之类的占位语句)

### 重试逻辑

3次重试，每次间隔递增。捕获 `APIConnectionError` 和 `APIError`。

## AI 验证器 (ai_validator.py)

3层验证管道：
1. **JSON 解析** — `json.loads()` 解析AI输出
2. **Schema 验证** — 检查 narrative(str), options(list), 每个option含 id+text
3. **业务验证** — 去重 option id, 限制选项数量(2-4个), 截断过长文本

验证失败静默 `pass` (8处 `except` — 已知技术债)。

## 生命阶段 (life_stage.py)

### LifeStage 枚举

```python
class LifeStage(Enum):
    INFANT = "infant"       # 0-3岁
    CHILD = "child"         # 4-11岁
    YOUTH = "youth"         # 12-15岁
    CULTIVATOR = "cultivator"  # 16+
```

### 关键函数

| 函数 | 返回值 | 说明 |
|------|--------|------|
| `get_life_stage(age)` | LifeStage | 按年龄返回对应阶段 |
| `get_cultivation_multiplier(age)` | float | 修炼乘数: INFANT/CHILD=0.0, YOUTH=0.5, CULTIVATOR=1.0 |
| `can_attempt_breakthrough(age)` | bool | 仅 16+ 可突破 |
| `get_breakthrough_penalty(age)` | float | 未成年突破惩罚 0.5 |

- INFANT/CHILD 阶段修炼收益为 0（只能通过事件获得修为）
- YOUTH 阶段修炼效率 50%，可触发少年事件
- CULTIVATOR 阶段完全体修炼效率
- `life_stage.py` 被 `game_service.py` 和 `event_engine.py` 引用

## 突破系统 (breakthrough.py)

### BreakthroughResult (dataclass)

```python
@dataclass
class BreakthroughResult:
    success: bool
    new_realm: str
    cultivation_loss: float
    realm_dropped: bool
    ascended: bool
```

### 核心逻辑

- `attempt_breakthrough(current_realm, cultivation, talents, pill_used)` → BreakthroughResult
- 成功率: 基础50% - 境界惩罚(REALM_PENALTY) + 天赋加成(百折不挠 +10%) + 丹药加成(+15%)
- 失败: 损失 cultivation (30-50%)，可能掉境界
- 最高境界"渡劫飞升"设置 `ascended=True`

### 突破交互流程（新模式）

突破不再是在 process_choice 中自动处理，而是作为**独立交互事件**：
1. `_ensure_pending_breakthrough()` 在修炼溢出后设置 `_pending_breakthrough` flag（存在 state dict 中，不存 DB）
2. 下一次 `get_next_event()` 检测到 flag → 调用 `build_breakthrough_event()` 生成含两选项的事件（use_pill / direct）
3. 前端进入 `breakthrough_choosing` 阶段，展示突破选项卡片
4. `process_choice()` 检测到突破事件 → 调用 `handle_breakthrough_choice()` → 调用 `attempt_breakthrough()`
5. 结果 aftermatth 持久化到 EventLogEntry，前端回到正常事件流

## 缓存服务 (cache_service.py)

双层缓存架构：
- **Layer 1**: 内存 LRU (OrderedDict, 最大100条, TTL 30分钟)
- **Layer 2**: SQLite 表 (cache_entries: key, response_json, created_at)

## YAML 数据服务 (realm/sect/talent)

三个服务共享相同模式：
1. 模块级 `_cache` 变量
2. `load_*()` → YAML safe_load + 缓存
3. `get_*_config(name)` → 查找特定配置
4. 路径: `os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "*.yaml")`

## 测试覆盖

`tests/test_services/` 包含 9 个测试文件，每个服务一个：
- Mock 模式: MockAIService 替代真实AI调用
- 随机种子: `random.seed(42)` 确保确定性
- 辅助函数: 每个文件内联 `_make_player()`, `_make_settings()` 工厂

## 注意事项

- `game_service.py` 是**最大的单文件** (629行)，承担了编排+后果叙事+修炼计算等职责
- 所有服务都是**模块级函数**，不是类 (除 BreakthroughResult dataclass)
- 状态在内存 `_games` dict 和 SQLite 间同步，无事务保证
- `except Exception: pass` 有8处，建议统一改为 `logger.warning()`
