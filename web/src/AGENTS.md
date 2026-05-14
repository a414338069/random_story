# AGENTS.md — 前端架构 (web/src/)

> 层次化知识库 · 自动生成 · 面向 AI Agent 导航

## 概览

Vue 3 + NaiveUI + TypeScript 前端，使用 `<script setup>` SFC 和组合式函数模式。Vite 构建工具。

## 目录结构

```
web/src/
├── main.ts                 # 入口: createApp + NaiveUI + Router
├── App.vue                 # 根组件: NConfigProvider + NMessageProvider + RouterView
├── router.ts               # Vue Router: 4个路由 (/, /game, /talents, /gameover)
├── api/                    # API 客户端层
│   ├── client.ts           # fetch 封装 (VITE_API_BASE 前缀)
│   ├── game.ts             # 游戏 API 调用函数
│   └── __tests__/          # API 测试 (mock fetch)
├── composables/            # Vue 组合式函数 (核心逻辑)
│   ├── useGameLoop.ts      # ★ 游戏主循环 (事件获取+选择+突破)
│   ├── useGameState.ts     # 游戏状态管理 (reactive state)
│   ├── useTypewriter.ts    # 打字机效果动画
│   ├── useAnimatedNumber.ts # 数字滚动动画
│   ├── useErrorHandler.ts  # 统一错误处理
│   └── __tests__/          # composable 测试
├── components/             # UI 组件
│   ├── StatusBar.vue       # 状态栏 (境界/修炼/年龄/灵石)
│   ├── NarrativeLog.vue    # 历史叙事滚动列表
│   ├── OptionCard.vue      # 选项卡片 (点击选择)
│   ├── PlayerStatusPanel.vue # 玩家状态面板 (详细属性展示)
│   ├── TalentCard.vue      # 天赋卡片 (选择/展示)
│   ├── AttributeAllocator.vue # 属性分配器 (10点四维)
│   ├── LeaderboardModal.vue # 排行榜弹窗
│   └── LoadingOverlay.vue  # 加载遮罩
├── views/                  # 页面视图
│   ├── TitleScreen.vue     # 首页 (开始游戏)
│   ├── TalentSelect.vue    # 天赋选择页 (抽卡+选择3张)
│   ├── GameMain.vue        # ★ 游戏主页 (核心UI)
│   └── GameOver.vue        # 结算页 (评分+评级+结局)
├── core/                   # 类型 + 工具
│   ├── types.ts            # ★ 核心类型定义
│   ├── normalize.ts        # 数据标准化 (API → 前端格式)
│   ├── talents.ts          # 天赋数据工具
│   └── __tests__/          # core 测试
├── data/                   # 静态数据
│   └── talents.ts          # 前端天赋展示数据
└── styles/                 # 样式
    ├── variables.css       # CSS 变量 (颜色/间距)
    ├── animations.css      # CSS 动画 (脉冲/渐入/闪烁)
    ├── mobile.css          # 移动端适配
    └── theme.ts            # NaiveUI 主题配置
```

## 核心类型 (core/types.ts)

```typescript
interface PlayerState {
  id: string
  name: string
  gender: string
  realm: string
  realm_progress: number
  cultivation: number
  age: number
  health: number
  qi: number
  lifespan: number
  faction: string
  spirit_stones: number
  techniques: Technique[]
  inventory: string[]
  event_count: number
  score: number
  is_alive: boolean
}

interface EventLogEntry {
  age: number
  narrative: string
  chosen_text: string
  consequence_narrative: string
  cultivation_change: number
  spirit_stones_change: number
  phase: 'normal' | 'breakthrough' | 'quiet_year' | 'breakthrough_choosing'  // 事件阶段
}

interface BreakthroughInfo {
  message: string
  new_realm: string | null
  success: boolean | null
}
```

## 页面流程

```
TitleScreen → TalentSelect → GameMain → GameOver
    (/)           (/talents)    (/game)    (/gameover)
```

### TitleScreen.vue
- 输入玩家名 + 选择性别
- "开始游戏" → `POST /api/v1/game/start`

### TalentSelect.vue
- 抽取天赋卡 (5张随机)
- 选择3张
- 属性分配 (10点四维: 根骨/悟性/心性/运气)
- "进入游戏" → 导航到 `/game`

### GameMain.vue ★
- **核心游戏界面**
- StatusBar (顶部) + NarrativeLog (中间) + OptionCard (底部)
- 游戏循环由 `useGameLoop` composable 驱动
- 突破: 突破作为独立交互事件，前端进入 `breakthrough_choosing` 阶段，展示选项卡片 (use_pill/direct)
- 突破等待: 选择后进入 `waiting_click` 模式 + 金色脉冲动画 + "点击继续"
- 安静年: 仅显示叙事，无选项卡片

### GameOver.vue
- 显示结局、评分、评级 (SSS~D)
- 排行榜入口
- "再来一局" → 回到 TitleScreen

## 游戏主循环 (useGameLoop.ts)

### 状态机

```
IDLE → FETCHING_EVENT → SHOWING_EVENT → CHOOSING → PROCESSING
                                                        ↓
                                          BREAKTHROUGH_CHOOSING (可选) → PROCESSING
                                                        ↓
                                              BREAKTHROUGH_WAIT (可选)
                                                        ↓
                                                     IDLE
```

### 关键函数

| 函数 | 职责 |
|------|------|
| `fetchNextEvent()` | 调用 `POST /api/v1/game/event` 获取下一事件 |
| `chooseOption(optionId)` | 调用 `POST /api/v1/game/event/choose` 处理选择 |
| `handleBreakthroughClick()` | 突破预警时触发 → 调用 `getNextEvent` 获取突破事件 |
| `confirmBreakthroughChoice(optionId)` | 突破选择提交 → 调用 `chooseOption` 处理 use_pill/direct |
| `handleBreakthrough()` | 处理突破动画 → 等待玩家点击 → 继续 |
| `checkGameOver()` | 检查 `is_alive` 和 `age >= lifespan` |

### 突破流程（新模式）

突破作为独立交互事件分两步：

**第一步 — 突破选择：**
1. `getNextEvent` 返回突破事件（`_pending_breakthrough` flag 触发）
2. 前端进入 `BREAKTHROUGH_CHOOSING` 阶段，显示含选项的突破叙事
3. 选项: `use_pill`（消耗丹药+15%成功率）或 `direct`（直接突破，无加成）
4. 玩家选择 → `confirmBreakthroughChoice(optionId)` → `POST /event/choose`

**第二步 — 突破结果：**
5. `chooseOption` 返回突破结果（成功/失败）
6. 设置 `waiting_click = true`, 显示金色脉冲动画 + 结果文本
7. 玩家点击"点击继续"
8. 动画完成 → aftermath 持久化到 EventLogEntry → 继续获取下一事件`

## API 客户端 (api/)

### client.ts

```typescript
// 所有请求经过此封装
const BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T>
```

### game.ts

| 函数 | API 端点 |
|------|---------|
| `startGame(req)` | `POST /api/v1/game/start` |
| `getGameState(id)` | `GET /api/v1/game/state/{id}` |
| `getNextEvent(playerId)` | `POST /api/v1/game/event` |
| `chooseOption(sessionId, optionId)` | `POST /api/v1/game/event/choose` |
| `endGame(sessionId)` | `POST /api/v1/game/end` |
| `getLeaderboard()` | `GET /api/v1/game/leaderboard` |

## 组件设计模式

### 通用模式

- **Props down, Events up**: 父组件通过 props 传数据，子组件通过 emit 通知
- **Composable 抽象**: 复杂逻辑抽取到 `composables/`，组件只管渲染
- **NaiveUI 组件**: 统一使用 `n-` 前缀组件 (`n-button`, `n-card`, `n-progress` 等)

### 数据标准化 (normalize.ts)

API 返回的 snake_case 字段转换为 camelCase，处理字段缺失和类型转换。

## 样式系统

### CSS 变量 (variables.css)

```css
:root {
  --primary-color: #...     /* 主色调 */
  --bg-color: #...          /* 背景色 */
  --text-color: #...        /* 文字色 */
  --gold-color: #...        /* 金色 (突破动画) */
}
```

### 动画 (animations.css)

- `pulse-gold`: 金色脉冲 (突破时用)
- `fade-in`: 渐入效果
- `typewriter-cursor`: 打字机光标闪烁

### 移动端适配 (mobile.css)

- 375px 基准宽度
- 触摸友好的按钮尺寸 (≥44px)
- NarrativeLog 滚动优化

## 测试

- **单元测试**: `__tests__/` 目录，Vitest + jsdom
- **E2E测试**: `web/e2e/` 目录，Playwright
- **Mock模式**: `vi.fn()` mock fetch，`vi.useFakeTimers()` mock 定时器
- **运行**: `cd web && npm run test:unit` / `npm run test:e2e`

## 已知问题

- `AttributeAllocator.vue`: 3处 `key as any` (模板 v-for 类型问题)
- `TalentSelect.vue`: 1处 `catch (err: any)` (错误类型未定义)
- 无全局错误边界 (ErrorBoundary)
- 无 Pinia/Vuex — 状态通过 props + composables 的 reactive 管理
