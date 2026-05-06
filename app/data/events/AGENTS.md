# AGENTS.md — 事件模板系统 (app/data/events/)

> 层次化知识库 · 自动生成 · 面向 AI Agent 导航

## 概览

76 YAML 事件模板，是游戏随机事件的核心数据源。每个模板定义触发条件、叙事提示、默认选项和后果。

## 文件清单

### 事件分类 (16 大类)

| 类别 | 文件数 | 前缀 | 触发场景 |
|------|--------|------|---------|
| daily | 15 | `daily_001` ~ `daily_015` | 日常修行生活 |
| childhood | 10 | `childhood_001` ~ `childhood_010` | 童年事件 (4-11岁) |
| adventure | 8 | `adventure_001` ~ `adventure_008` | 探险奇遇 |
| bottleneck | 6 | `bottleneck_000` ~ `bottleneck_005` | 瓶颈/突破契机 |
| stones | 5 | `stones_001` ~ `stones_005` | 灵石相关 |
| combat | 4 | `combat_001` ~ `combat_004` | 战斗冲突 |
| social | 4 | `social_001` ~ `social_004` | 社交互动 |
| economy | 4 | `economy_001` ~ `economy_004` | 经济/交易 |
| explore | 4 | `explore_001` ~ `explore_004` | 探索/发现 |
| youth | 4 | `youth_001` ~ `youth_004` | 少年事件 (12-15岁) |
| fortune | 3 | `fortune_001` ~ `fortune_003` | 际遇/机缘 |
| sect | 3 | `sect_001` ~ `sect_003` | 门派相关 |
| emotional | 2 | `emotional_001` ~ `emotional_002` | 情感/心魔 |
| heavenly | 2 | `heavenly_001` ~ `heavenly_002` | 天劫/天赐 |
| birth | 2 | `birth_001` ~ `birth_002` | 出生事件 (0-3岁) |

### 测试文件

- `_test_daily.yaml` — 日常事件测试模板
- `_test_jindan.yaml` — 金丹期测试模板

## YAML 模板 Schema

```yaml
id: "daily_001"           # 唯一标识符 (类型_编号)
type: "daily"              # 事件类型 (14大类之一)
title: "砍柴挑水"          # 事件标题
trigger_conditions:        # 触发条件
  min_realm: "凡人"        # 最低境界 (null = 无限制)
  max_realm: "凡人"        # 最高境界 (null = 无限制)
  min_age: 5               # 最小年龄
  max_age: 15              # 最大年龄
  required_faction: null   # 需要的门派 (null = 无要求)
weight: 1.0                # 基础权重 (越高越常触发)
prompt_template: "..."      # AI叙事生成提示词
fallback_narrative: "..."   # AI失败时的备用叙事
default_options:            # 默认选项 (2-4个)
  - id: "opt1"
    text: "继续劳作"
    consequences:
      cultivation_gain: 5
      age_advance: true
  - id: "opt2"
    text: "偷偷修炼"
    consequences:
      cultivation_gain: 10
      age_advance: true
```

## 触发条件说明

### 境界匹配

- `min_realm` / `max_realm`: 使用 `realms.yaml` 中的 `order` 字段比较
- 玩家境界 order 必须在 [min_order, max_order] 范围内
- `null` 表示不限制

### 年龄匹配

- `min_age` / `max_age`: 直接整数比较
- `null` 表示不限制

### 门派匹配

- `required_faction`: 精确匹配玩家 faction 字段
- `null` 表示任何门派都可以触发

## 权重系统

`event_engine.calculate_weights()` 调整权重：

1. **基础权重**: YAML `weight` 字段 (通常 0.5 ~ 2.0)
2. **运气修正**: `luck * 0.05` 加成
3. **修炼进度修正**: cultivation 接近突破时增加 adventure/combat 权重
4. **防重复**: `should_force_non_daily()` — 连续3+ daily 后强制降低 daily 权重

## 安静年 (Quiet Year)

不由 YAML 定义，而是由 `event_engine._build_quiet_year_event()` 动态生成：
- 触发条件: 连续 ≥2 个有选项事件后，25% 概率（不受生命阶段影响，各阶段均可触发）
- 内容: 从预设叙事列表随机选择
- 特征: `narrative_only` = true, 无 `options`

## 生命阶段相关事件

事件模板按生命阶段设计：
- **birth** (0-3岁): 出生初始事件
- **childhood** (4-11岁): 童年生活事件，`min_age` 全部设为 4-11 或覆盖 4+（部分模板原 `min_age=0` 改为 `min_age=12` 避免童年期误触发）
- **youth** (12-15岁): 少年事件，修炼乘数 0.5 阶段专属事件
- **daily/adventure 等** (16+): 核心修仙事件，部分原 `min_age=0` 模板调整为 `min_age=12` 以适应生命阶段划分

事件引擎根据 `player_state.age` 自动筛除不匹配年龄的模板。

## 新增事件模板指南

### 步骤

1. 确定类别和编号 (如 `social_005`)
2. 创建 `app/data/events/{category}_{num}.yaml`
3. 遵循上述 YAML Schema
4. 确保 `trigger_conditions` 合理 (参考 `realms.yaml` 的 order 值)
5. 运行 `uv run python -m app.data.validate_data` 验证

### 命名规范

- 文件名: `{category}_{NNN}.yaml` (3位数字，左补零)
- id: 与文件名一致
- type: 与 category 一致

### 后果值范围

- `cultivation_gain`: 0 ~ 50 (一般事件), 50 ~ 200 (重大事件)
- `spirit_stones_gain`: -100 ~ 100 (AI 可调整，白名单限制)
- `age_advance`: 通常 `true`

## 相关代码

- `app/services/event_engine.py` — 模板加载、筛选、权重计算
- `app/data/realms.yaml` — 境界配置 (用于条件匹配)
- `app/data/validate_data.py` — 数据校验 CLI
