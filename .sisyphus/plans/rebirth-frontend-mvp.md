# 重生模拟器 — 前端 MVP 开发计划

## TL;DR

> **核心目标**：为"重生模拟器"AI文字修仙游戏构建前端 MVP，实现完整游戏循环（标题→天赋选择→事件循环→结算评分）
>
> **Deliverables**:
> - Vue3 + Vite + TypeScript + Naive UI 前端项目
> - 4 个页面视图（TitleScreen / TalentSelect / GameMain / GameOver）
> - 状态机驱动的事件循环 + 打字机叙事效果
> - 对接后端 6 个 API 端点（统一处理双状态格式）
> - 水墨古风主题 + 移动端响应式
> - Vitest 单元测试 + Playwright E2E 测试
>
> **Estimated Effort**: Medium（~19h 编码 + 3h 测试）
> **Parallel Execution**: YES - 5 Waves
> **Critical Path**: 脚手架 → 类型定义 → API客户端 → 天赋数据 → 游戏主循环 → 主题美化 → 测试

---

## Context

### Original Request
用户要求为"重生模拟器"AI文字修仙游戏开发前端 MVP。后端已完成（383 tests passed, 6 API endpoints），前端从零开始。

### Interview Summary
**Key Discussions**:
- 用户授权全自主执行（去休息，全部信任AI）
- 所有决策以推荐为主
- 高精度 Momus 审查
- 直接授权 /start-work
- 所有文档复制到 Obsidian 笔记
- 前端放在同一仓库 `web/` 子目录

**Research Findings**:
- Oracle 全面评审了8个架构维度，确认 core/composables/views 三层结构
- 后端 API 合同完全映射：6 端点，2 种不同状态格式需前端统一处理
- game-architect skill 确认 DOM 渲染完全适合文字游戏
- 后端 CORS 完全开放（allow_origins=["*"]）

### Metis Review
**Identified Gaps** (addressed):
- 🚨 后端无天赋抽卡 API → 前端内嵌 talents.json 静态数据，客户端实现抽卡
- 🟡 天赋效果未在后端生效 → 前端不展示数值效果细节，只展示名称/品级/类别/描述
- 🟡 突破系统未接入游戏循环 → 不做突破 UI
- 🟢 health/qi 字段始终为默认值 → 不展示 HP/Qi 进度条
- 🟡 排行榜返回空数组 → 展示"暂无记录"空状态

---

## Work Objectives

### Core Objective
构建可支撑完整单局游戏体验的 Web 前端——从标题画面到天赋选择到事件循环到结算评分，含水墨古风主题和移动端适配。

### Concrete Deliverables
- `web/` 目录下的 Vue3 + Vite + TypeScript 项目
- TitleScreen.vue — 标题画面 + "开始修仙" 按钮
- TalentSelect.vue — 天赋抽卡(3张) + 属性分配(10点)
- GameMain.vue — 核心事件循环（状态机：fetching→typing→choosing→submitting→aftermath）
- GameOver.vue — 结算评分 + 结局展示 + 再来一局
- API 客户端 — 统一处理后端双状态格式
- 水墨古风主题 — Naive UI themeOverrides + CSS 变量
- 移动端响应式 — 375px 宽度起适配

### Definition of Done
- [x] `pnpm dev` 启动无错误，可通过浏览器访问
- [x] 完整游戏循环可通过 UI 端到端走通（创建角色→天赋选择→事件循环→结算）
- [x] 移动端（375px）无水平滚动，所有交互正常
- [x] 后端 AI 不可用时（fallback），前端仍可正常游戏
- [x] 网络错误时展示友好提示，不白屏不崩溃

### Must Have
- 前端项目在 `web/` 子目录（与后端同仓库）
- Vite 代理配置 `/api` → 后端 `localhost:8000`
- TypeScript 严格模式，所有 API 响应有类型定义
- 后端双状态格式统一为 `NormalizedGameState`
- 天赋卡数据内嵌为 `src/data/talents.ts`（20张）
- 事件循环状态机：idle/fetching/typing/choosing/submitting/aftermath/gameover
- 打字机效果用 requestAnimationFrame（非 setInterval）
- 选项点击跳过打字机效果
- Vue Router 4 个路由 + beforeEach 守卫
- Naive UI 组件库 + 水墨古风主题覆盖
- 所有 API 错误有友好提示（网络/404/500）
- 移动端优先响应式设计

### Must NOT Have (Guardrails)
- ❌ 后端代码修改（后端已冻结）
- ❌ Pinia/Vuex 状态管理（reactive() 够用）
- ❌ Canvas/WebGL/游戏引擎
- ❌ HP/Qi 进度条展示（后端始终为默认值）
- ❌ 天赋卡数值效果展示（后端未实现）
- ❌ 突破系统 UI（后端未接入）
- ❌ 音效/背景音乐
- ❌ localStorage 游戏存档持久化
- ❌ 离线模式
- ❌ 设置/偏好页面
- ❌ 分享功能（图片渲染）
- ❌ 暗色模式切换
- ❌ 自定义字体加载
- ❌ 国际化 i18n（仅中文）
- ❌ 微信小游戏适配（V1.5）
- ❌ NPC/善恶/轮回系统 UI
- ❌ 平台抽象层/适配器模式（过度工程）
- ❌ 动画库（仅 CSS transition + keyframes）

---

## Verification Strategy (MANDATORY)

> **ZERO HUMAN INTERVENTION** - ALL verification is agent-executed.

### Test Decision
- **Infrastructure exists**: NO（新前端项目，搭建中配置）
- **Automated tests**: YES (tests-after)
- **Framework**: Vitest + Playwright
- **If TDD**: 不使用 TDD，实现后补测试

### QA Policy
Every task MUST include agent-executed QA scenarios.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **组件/页面**: Playwright — 导航、交互、断言 DOM
- **API 客户端**: Vitest — mock fetch，验证类型转换
- **游戏循环**: Playwright — 完整游戏流程 E2E
- **主题/响应式**: Playwright — 截图对比不同视口

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation — sequential, 4 tasks):
├── Task 1: Vite+Vue3+TS+NaiveUI 脚手架 + Vite 代理 [quick]
├── Task 2: TypeScript 类型定义（双状态+统一格式） [quick]
├── Task 3: API 客户端 + normalizeState() + 错误处理 [quick]
└── Task 4: Vue Router + App.vue 布局壳 + 导航守卫 [quick]

Wave 2 (Data + Composables — parallel, 3 tasks):
├── Task 5: 天赋卡静态数据 + 抽卡逻辑 [quick]
├── Task 6: useGameState composable（reactive 全局状态） [quick]
└── Task 7: useTypewriter composable（rAF 打字机） [quick]

Wave 3 (Views — partial parallel, 4 tasks):
├── Task 8: TitleScreen 视图 (depends: 4) [visual-engineering]
├── Task 9: TalentSelect 视图 — 抽卡+属性分配 (depends: 4,5,6) [visual-engineering]
├── Task 10: GameMain 视图 — 事件循环核心 (depends: 3,4,6,7) [deep]
└── Task 11: GameOver 视图 — 结算+评分 (depends: 4,6) [visual-engineering]

Wave 4 (Polish — parallel, 3 tasks):
├── Task 12: 水墨古风主题 — NConfigProvider + CSS 变量 (depends: 8-11) [visual-engineering]
├── Task 13: 移动端响应式适配 (depends: 10) [visual-engineering]
└── Task 14: 错误处理完善 + Loading 状态 (depends: 10) [quick]

Wave 5 (Testing + Integration):
├── Task 15: Vitest 单元测试 — normalizeState + typewriter + API client (depends: 3,7) [unspecified-high]
├── Task 16: Playwright E2E — 完整游戏流程 (depends: all) [deep]
└── Task 17: 后端联调 + 修复 (depends: 16) [unspecified-high]

Wave FINAL (Review — 4 parallel):
├── F1: Plan compliance audit (oracle)
├── F2: Code quality review (unspecified-high)
├── F3: Real manual QA — 完整游戏体验 (unspecified-high)
└── F4: Scope fidelity check (deep)
→ Present results → Get user okay

Critical Path: T1→T2→T3→T6→T10→T16→F1-F4
Parallel Speedup: ~50% faster than sequential
Max Concurrent: 4 (Wave 3)
```

### Dependency Matrix

| Task | Depends On | Blocks | Wave |
|------|-----------|--------|------|
| 1 | - | 2,3,4 | 1 |
| 2 | 1 | 3 | 1 |
| 3 | 1,2 | 10,15 | 1 |
| 4 | 1 | 8,9,10,11 | 1 |
| 5 | 1 | 9 | 2 |
| 6 | 1,3 | 9,10,11 | 2 |
| 7 | 1 | 10,15 | 2 |
| 8 | 4 | 12 | 3 |
| 9 | 4,5,6 | 12 | 3 |
| 10 | 3,4,6,7 | 12,13,14,16 | 3 |
| 11 | 4,6 | 12 | 3 |
| 12 | 8,9,10,11 | - | 4 |
| 13 | 10 | - | 4 |
| 14 | 10 | - | 4 |
| 15 | 3,7 | - | 5 |
| 16 | all | 17 | 5 |
| 17 | 16 | F1-F4 | 5 |

### Agent Dispatch Summary

- **Wave 1**: 4 tasks → all `quick`
- **Wave 2**: 3 tasks → all `quick`
- **Wave 3**: 4 tasks → T8 `visual-engineering`, T9 `visual-engineering`, T10 `deep`, T11 `visual-engineering`
- **Wave 4**: 3 tasks → T12 `visual-engineering`, T13 `visual-engineering`, T14 `quick`
- **Wave 5**: 3 tasks → T15 `unspecified-high`, T16 `deep`, T17 `unspecified-high`
- **FINAL**: 4 tasks → F1 `oracle`, F2 `unspecified-high`, F3 `unspecified-high`, F4 `deep`

---

## TODOs

- [x] 1. Vite+Vue3+TS+NaiveUI 脚手架 + Vite 代理

  **What to do**:
  - 在项目根目录创建 `web/` 子目录
  - 用 `pnpm create vite web --template vue-ts` 初始化
  - 安装依赖：`naive-ui`, `vue-router@4`, `@vicons/ionicons5`
  - 安装开发依赖：`vitest`, `@vue/test-utils`, `playwright`, `@playwright/test`
  - 配置 `vite.config.ts`：proxy `/api` → `http://localhost:8000`
  - 配置 `tsconfig.json`：strict mode, paths alias `@/` → `src/`
  - 创建基础目录结构：`src/{core,composables,views,components,api,data,styles}`
  - 清理默认模板文件
  - 更新根 `.gitignore` 添加 `web/node_modules/`, `web/dist/`

  **Must NOT do**:
  - 不修改后端代码
  - 不配置 Docker
  - 不安装 Pinia

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1 (sequential, first)
  - **Blocks**: Tasks 2, 3, 4
  - **Blocked By**: None

  **References**:
  - **Pattern**: tech doc §1.2 项目结构 — `rebirth-simulator/src/` 完整目录布局
  - **External**: Vite 官方文档 — proxy 配置 `server.proxy`
  - **External**: Naive UI 安装指南 — `pnpm add naive-ui`

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: 项目结构完整性
    Tool: Bash
    Steps:
      1. ls web/src/ → 包含 main.ts, App.vue, core/, composables/, views/, components/, api/, data/, styles/
      2. cat web/package.json → 包含 naive-ui, vue-router, vitest 依赖
      3. cat web/vite.config.ts → 包含 proxy /api 配置
    Expected: 所有目录和文件存在
    Evidence: .sisyphus/evidence/task-1-structure.txt

  Scenario: 开发服务器启动
    Tool: Bash
    Steps:
      1. cd web && pnpm install
      2. pnpm dev → 成功启动，输出 localhost URL
    Expected: 无错误，Vite dev server 启动成功
    Evidence: .sisyphus/evidence/task-1-dev-server.txt
  ```

  **Commit**: YES
  - Message: `feat(web): 初始化 Vue3+Vite+TS+NaiveUI 前端项目`
  - Files: `web/` 全部初始文件

- [x] 2. TypeScript 类型定义 — 双状态格式 + 统一 GameState

  **What to do**:
  - 创建 `web/src/core/types.ts`：
    - `PlayerStatePydantic` — 匹配 POST /start 返回的 PlayerState（扁平蛇形命名，含 health/qi/score/timestamps，无 cultivation/age）
    - `GameStateDict` — 匹配 GET /state 和 POST /choose 返回的内部 dict（嵌套驼峰 attributes，含 cultivation/age/ascended/technique_grades，无 health/qi/score）
    - `NormalizedGameState` — 前端统一使用的游戏状态（合并两格式所有有用字段）
    - `EventResponse`, `EventOption`, `ChooseResponse`, `GameStartRequest`, `GameStartResponse`, `EndGameResponse`, `LeaderboardEntry`
    - `Attributes` — { rootBone, comprehension, mindset, luck }
    - `TalentCard` — { id, name, grade, rarity, category, description }
    - `LoopPhase` — 'idle' | 'fetching' | 'typing' | 'choosing' | 'submitting' | 'aftermath' | 'gameover'
  - 创建 `web/src/core/normalize.ts`：
    - `normalizeFromPydantic(state: PlayerStatePydantic): NormalizedGameState`
    - `normalizeFromDict(state: GameStateDict): NormalizedGameState`
    - 两个函数都输出统一的 NormalizedGameState

  **Must NOT do**:
  - 不安装额外类型库
  - 不创建运行时校验（zod等）

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1 (sequential, after Task 1)
  - **Blocks**: Task 3
  - **Blocked By**: Task 1

  **References**:
  - **Pattern**: 后端 `app/models/player.py` PlayerState — 所有字段名和类型
  - **Pattern**: 后端 `app/services/game_service.py` 内部 dict — 嵌套 attributes, cultivation, age, ascended
  - **Metis 关键发现**: POST /start 和 GET /state 返回不同格式，前端必须统一

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: 类型编译
    Tool: Bash
    Steps:
      1. cd web && pnpm vue-tsc --noEmit
      2. 无类型错误
    Expected: 0 errors
    Evidence: .sisyphus/evidence/task-2-types.txt
  ```

  **Commit**: YES
  - Message: `feat(web): TypeScript 类型定义 — 双状态格式 + 统一 GameState`
  - Files: `web/src/core/types.ts, web/src/core/normalize.ts`

- [x] 3. API 客户端 + normalizeState() + 错误处理

  **What to do**:
  - 创建 `web/src/api/client.ts`：
    - 封装 fetch：baseURL, Content-Type, 错误处理
    - 统一错误类型：`FetchError { status, message, code }`
    - 超时设置：10s
  - 创建 `web/src/api/game.ts`：
    - `startGame(req: GameStartRequest): Promise<{ sessionId, state }>` — POST /start, normalize state
    - `getEvent(sessionId: string): Promise<EventResponse>` — POST /event
    - `chooseOption(sessionId: string, optionId: string): Promise<ChooseResponse>` — POST /choose, normalize state
    - `getState(sessionId: string): Promise<NormalizedGameState>` — GET /state, normalize
    - `endGame(sessionId: string): Promise<EndGameResponse>` — POST /end
    - `getLeaderboard(): Promise<LeaderboardEntry[]>` — GET /leaderboard
  - 所有 API 函数返回 NormalizedGameState（统一格式）

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1 (sequential, after Task 2)
  - **Blocks**: Tasks 6, 10, 15
  - **Blocked By**: Tasks 1, 2

  **References**:
  - **API**: 后端 6 端点签名 — 见 Metis 评审中 "Verified API Contract" 完整表
  - **Pattern**: `web/src/core/normalize.ts` — 所有 API 函数调用 normalize 转换

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: API 客户端类型安全
    Tool: Bash
    Steps:
      1. pnpm vue-tsc --noEmit → 无错误
      2. 所有 6 个 API 函数有正确的 TypeScript 签名
    Expected: 类型检查通过
    Evidence: .sisyphus/evidence/task-3-api-types.txt
  ```

  **Commit**: YES
  - Message: `feat(web): API 客户端 + normalizeState + 错误处理`
  - Files: `web/src/api/client.ts, web/src/api/game.ts`

- [x] 4. Vue Router + App.vue 布局壳 + 导航守卫

  **What to do**:
  - 创建 `web/src/router.ts`：
    - 4 路由：`/`(TitleScreen), `/select`(TalentSelect), `/game`(GameMain), `/gameover`(GameOver)
    - beforeEach 守卫：检查 sessionId 存在（meta.requiresSession）
  - 更新 `web/src/App.vue`：`<RouterView />` + `<Transition>` 包裹
  - 更新 `web/src/main.ts`：注册 router + NaiveUI NConfigProvider

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1 (sequential, after Task 1)
  - **Blocks**: Tasks 8, 9, 10, 11
  - **Blocked By**: Task 1

  **References**:
  - **Pattern**: Oracle 建议 — Vue Router 而非条件渲染，beforeEach 守卫校验 session
  - **External**: Vue Router 4 文档 — 路由配置 + 导航守卫

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: 路由导航
    Tool: Bash
    Steps:
      1. pnpm dev → 启动
      2. 浏览器访问 / → 显示标题页（空白占位即可）
      3. 直接访问 /game → 被守卫重定向到 /
    Expected: 路由工作正常
    Evidence: .sisyphus/evidence/task-4-router.txt
  ```

  **Commit**: YES
  - Message: `feat(web): Vue Router + 4 路由 + 导航守卫`
  - Files: `web/src/router.ts, web/src/App.vue, web/src/main.ts`

- [x] 5. 天赋卡静态数据 + 抽卡逻辑

  **What to do**:
  - 创建 `web/src/data/talents.ts`：
    - 内嵌 20 张天赋卡数据（从后端 `app/data/talents.yaml` 转换）
    - 每张卡：id, name, grade, rarity, category, description（不含 effects 详情，因为后端未实现）
    - 品级颜色映射：凡品(灰白), 灵品(青绿), 玄品(靛蓝), 仙品(紫金), 神品(金辉)
  - 创建 `web/src/core/talents.ts`：
    - `drawCards(count: number): TalentCard[]` — 按 rarity 加权随机抽卡
    - `getGradeColor(grade: string): string` — 品级对应颜色
    - `canReDraw(currentCards, allCards, reDrawCount, maxReDraw): TalentCard[]` — 重抽逻辑

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 6, 7)
  - **Blocks**: Task 9
  - **Blocked By**: Task 1

  **References**:
  - **Pattern**: 后端 `app/data/talents.yaml` — 20 张天赋卡完整数据
  - **Pattern**: MVP doc §2.4 天赋卡 — 品级概率：凡品40%/灵品30%/玄品20%/仙品8%/神品2%
  - **Metis 建议**: 前端内嵌天赋数据，不依赖后端 API

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: 天赋卡数据完整性
    Tool: Bash
    Steps:
      1. 读取 talents.ts → 确认 20 张卡
      2. 每张卡包含 id, name, grade, category, description
      3. 品级分布：凡品6/灵品6/玄品4/仙品3/神品1
    Expected: 数据完整
    Evidence: .sisyphus/evidence/task-5-talents.txt

  Scenario: 抽卡逻辑
    Tool: Bash
    Steps:
      1. 调用 drawCards(3) → 返回 3 张卡
      2. 调用 100 次统计品级分布 → 大致符合权重
    Expected: 抽卡正常工作
    Evidence: .sisyphus/evidence/task-5-draw.txt
  ```

  **Commit**: YES
  - Message: `feat(web): 天赋卡静态数据 + 品级抽卡逻辑`
  - Files: `web/src/data/talents.ts, web/src/core/talents.ts`

- [x] 6. useGameState composable — reactive 全局状态

  **What to do**:
  - 创建 `web/src/composables/useGameState.ts`：
    - 模块级 `reactive<NormalizedGameState | null>(null)` 单例
    - `sessionId: ref<string | null>(null)`
    - `update(state: NormalizedGameState)` — 更新全局状态
    - `reset()` — 清空状态（返回标题页时）
    - `isAlive: computed` — is_alive 且 session 有效
    - `phase: ref<LoopPhase>('idle')` — 事件循环阶段

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 5, 7)
  - **Blocks**: Tasks 9, 10, 11
  - **Blocked By**: Tasks 1, 3

  **References**:
  - **Pattern**: tech doc §1.3 状态管理方案 — reactive() 单例，不需要 Pinia
  - **Pattern**: Oracle 建议 — useGameState 封装 reactive + computed

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: 状态更新
    Tool: Bash (vitest)
    Steps:
      1. 调用 update(mockNormalizedState)
      2. 读取 gameState.realm → "练气"
      3. 调用 reset()
      4. 读取 gameState → null
    Expected: 状态管理正确
    Evidence: .sisyphus/evidence/task-6-state.txt
  ```

  **Commit**: YES
  - Message: `feat(web): useGameState composable`
  - Files: `web/src/composables/useGameState.ts`

- [x] 7. useTypewriter composable — rAF 打字机效果

  **What to do**:
  - 创建 `web/src/composables/useTypewriter.ts`：
    - `displayed: ref<string>('')` — 当前显示文本
    - `isTyping: ref<boolean>(false)`
    - `isComplete: ref<boolean>(false)`
    - `typeText(text: string, charsPerSec?: number): Promise<void>` — rAF 驱动逐字显示
    - `skipToEnd()` — 跳过动画，直接显示全文
    - `cancel()` — 取消（组件卸载时调用）
    - 内部使用 requestAnimationFrame + delta time 计算
    - 后台标签页自动暂停（rAF 天然支持）

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 5, 6)
  - **Blocks**: Tasks 10, 15
  - **Blocked By**: Task 1

  **References**:
  - **Pattern**: Oracle 建议 — rAF 优于 setInterval（后台暂停、省电、同步渲染）
  - **Pattern**: game-architect skill — 对象池/帧循环模式参考

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: 打字机效果
    Tool: Bash (vitest, mock rAF)
    Steps:
      1. 调用 typeText("测试文本", 1000) // 1000字/秒（加速测试）
      2. 验证 displayed 逐步增长
      3. 调用 skipToEnd() → displayed = "测试文本"
    Expected: 打字机逻辑正确
    Evidence: .sisyphus/evidence/task-7-typewriter.txt
  ```

  **Commit**: YES
  - Message: `feat(web): useTypewriter composable — rAF 打字机效果`
  - Files: `web/src/composables/useTypewriter.ts`

- [x] 8. TitleScreen 标题画面

  **What to do**:
  - 创建 `web/src/views/TitleScreen.vue`：
    - 游戏标题"重生模拟器"（大字，水墨风格）
    - 副标题"AI修仙人生模拟器"
    - "开始修仙"按钮 → `router.push('/select')`
    - 底部"排行榜"链接（点击展示空状态"暂无记录"）
    - 简洁的水墨背景（CSS 渐变即可）

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: 页面需要视觉设计
  - **Skills**: [`frontend-design`, `karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 9, 10, 11)
  - **Blocks**: Task 12
  - **Blocked By**: Task 4

  **References**:
  - **Pattern**: MVP doc §五 Phase 1 — 开局流程入口

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: 标题页展示
    Tool: Playwright
    Steps:
      1. 导航到 /
      2. 验证标题包含"重生模拟器"
      3. 验证"开始修仙"按钮存在
      4. 点击按钮 → 导航到 /select
    Expected: 标题页正常工作
    Evidence: .sisyphus/evidence/task-8-title.png

  Scenario: 移动端标题页
    Tool: Playwright (375x812 viewport)
    Steps:
      1. 验证标题和按钮均可见
      2. 无水平滚动
    Expected: 移动端布局正常
    Evidence: .sisyphus/evidence/task-8-title-mobile.png
  ```

  **Commit**: YES
  - Message: `feat(web): TitleScreen 标题画面`
  - Files: `web/src/views/TitleScreen.vue`

- [x] 9. TalentSelect 天赋选择 + 属性分配

  **What to do**:
  - 创建 `web/src/views/TalentSelect.vue`：
    - 步骤 1：角色名输入 + 性别选择
    - 步骤 2：展示 3 张天赋卡（品级颜色编码）+ "重新抽取"按钮（最多重抽4次）
    - 步骤 3：10 点属性分配（根骨/悟性/心性/气运，滑块/+-按钮，总和=10时才能确认）
    - "确认"按钮 → 调用 `api.startGame()` → `router.push('/game')`
  - 创建 `web/src/components/TalentCard.vue`：天赋卡展示组件
  - 创建 `web/src/components/AttributeAllocator.vue`：属性分配组件

  **Must NOT do**:
  - 不展示天赋卡数值效果（后端未实现）
  - 不做翻卡动画（MVP 不做）

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-design`, `karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (after Tasks 4, 5, 6)
  - **Blocks**: Task 12
  - **Blocked By**: Tasks 4, 5, 6

  **References**:
  - **Pattern**: MVP doc §2.4 天赋卡 — 20 张卡品级/颜色/概率
  - **Pattern**: MVP doc §五 Phase 1 — 开局步骤 2-4
  - **Metis 建议**: 前端内嵌天赋数据，客户端抽卡

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: 完整天赋选择流程
    Tool: Playwright
    Steps:
      1. 导航到 /select
      2. 输入角色名 "测试仙人"
      3. 选择性别 "男"
      4. 验证 3 张天赋卡展示
      5. 点击"重新抽取" → 卡片变化
      6. 分配属性：根骨3/悟性3/心性2/气运2
      7. 点击确认 → 导航到 /game
    Expected: 完整流程正常
    Evidence: .sisyphus/evidence/task-9-talent-flow.png

  Scenario: 属性总和校验
    Tool: Playwright
    Steps:
      1. 分配属性总和 ≠ 10
      2. 验证确认按钮禁用
      3. 调整至总和 = 10
      4. 验证确认按钮启用
    Expected: 校验正确
    Evidence: .sisyphus/evidence/task-9-validation.png
  ```

  **Commit**: YES
  - Message: `feat(web): TalentSelect 天赋选择 + 属性分配`
  - Files: `web/src/views/TalentSelect.vue, web/src/components/TalentCard.vue, web/src/components/AttributeAllocator.vue`

- [x] 10. GameMain 事件循环核心 — 最关键任务

  **What to do**:
  - 创建 `web/src/composables/useGameLoop.ts`：
    - 状态机：idle → fetching → typing → choosing → submitting → aftermath → gameover
    - `advanceEvent()` — 调用 API 获取事件 → 启动打字机 → 切换到 choosing
    - `chooseOption(optionId)` — 提交选择 → 更新状态 → 展示 aftermath → 检查游戏结束 → 自动推进
    - 组件卸载时 cancel
  - 创建 `web/src/views/GameMain.vue`：
    - 顶部状态栏：境界(realm) | 年龄/寿命(age/lifespan) | 修为(cultivation) | 灵石(spirit_stones) | 事件数(event_count)
    - 叙事区域：打字机效果显示 narrative
    - 选项区域：2-3 个选项按钮（choosing 阶段淡入）
    - Loading 覆盖层：fetching 阶段显示"天命推演中…"
    - 后果反馈：aftermath 阶段显示"+X 修为，年龄增长 Y 岁"
  - 创建 `web/src/components/StatusBar.vue`：顶部状态栏组件
  - 创建 `web/src/components/NarrativeBox.vue`：叙事文本展示组件
  - 创建 `web/src/components/OptionCard.vue`：选项按钮组件
  - 创建 `web/src/components/LoadingOverlay.vue`：加载覆盖层

  **Must NOT do**:
  - 不展示 HP/Qi 进度条（始终默认值）
  - 不展示分数（仅在结算页）
  - 不做突破 UI（后端未接入）
  - 不使用 setInterval（必须用 rAF）

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: 事件循环状态机是前端最复杂的架构组件
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 8, 9, 11)
  - **Blocks**: Tasks 12, 13, 14, 16
  - **Blocked By**: Tasks 3, 4, 6, 7

  **References**:
  - **Pattern**: Oracle 建议 — 状态机驱动事件循环，6 个 phase
  - **Pattern**: tech doc §1.4 关键 UI 交互设计 — 叙事展示、状态栏、突破动画
  - **API**: 后端 POST /event 和 POST /choose — 请求/响应格式
  - **Metis 关键发现**: 后端返回 fallback 叙事，前端应静默接受不报错

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: 完整事件循环（需后端运行）
    Tool: Playwright
    Steps:
      1. 从 /select 完成天赋选择 → 进入 /game
      2. 等待 Loading 消失
      3. 验证叙事文本出现（打字机效果后）
      4. 验证 2-3 个选项按钮出现
      5. 点击第一个选项
      6. 验证状态栏更新（年龄增长）
      7. 等待下一个事件自动加载
    Expected: 事件循环正常工作
    Evidence: .sisyphus/evidence/task-10-event-loop.png

  Scenario: 选项点击跳过打字机
    Tool: Playwright
    Steps:
      1. 等待事件加载中
      2. 打字机开始时立即点击叙事区域
      3. 验证文本直接显示完整
    Expected: 跳过功能正常
    Evidence: .sisyphus/evidence/task-10-skip.txt

  Scenario: 网络错误处理
    Tool: Playwright
    Steps:
      1. 关闭后端
      2. 触发事件获取
      3. 验证错误提示出现（"天机紊乱"）
      4. 验证有重试选项
    Expected: 错误不导致白屏
    Evidence: .sisyphus/evidence/task-10-error.txt
  ```

  **Commit**: YES
  - Message: `feat(web): GameMain 事件循环核心`
  - Files: `web/src/composables/useGameLoop.ts, web/src/views/GameMain.vue, web/src/components/StatusBar.vue, web/src/components/NarrativeBox.vue, web/src/components/OptionCard.vue, web/src/components/LoadingOverlay.vue`

- [x] 11. GameOver 结算评分

  **What to do**:
  - 创建 `web/src/views/GameOver.vue`：
    - 结局类型（ending）：大字展示
    - 评分：score 数值 + grade 等级（SSS-D，颜色编码）
    - 角色摘要：姓名/门派/最高境界/享年
    - "再来一局"按钮 → reset 状态 → `router.push('/')`
    - "排行榜"按钮 → 显示排行榜（空状态"暂无记录"）
  - 结算数据来自 `useGameState` 或重新调用 `api.endGame()`

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-design`, `karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 8, 9, 10)
  - **Blocks**: Task 12
  - **Blocked By**: Tasks 4, 6

  **References**:
  - **Pattern**: MVP doc §五 Phase 6 — 结算界面设计
  - **Pattern**: spec doc §12.3 8 种结局 — 结局类型列表
  - **API**: POST /end 返回 `{session_id, ending, score, grade}`

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: 结算页展示
    Tool: Playwright
    Steps:
      1. 完成 1 局游戏（或模拟 is_alive=false 状态）
      2. 导航到 /gameover
      3. 验证结局类型显示
      4. 验证分数和等级显示
      5. 点击"再来一局" → 导航到 /
    Expected: 结算页正常
    Evidence: .sisyphus/evidence/task-11-gameover.png
  ```

  **Commit**: YES
  - Message: `feat(web): GameOver 结算评分`
  - Files: `web/src/views/GameOver.vue`

- [x] 12. 水墨古风主题

  **What to do**:
  - 创建 `web/src/styles/variables.css`：
    - CSS 自定义属性：墨黑 #2c2c2c, 宣纸白 #f5f0e8, 朱砂红 #c23a2b, 青黛 #4a7c7c
    - 字体栈：`"Noto Serif SC", "STSong", "SimSun", serif`
  - 更新 `App.vue`：Naive UI `NConfigProvider` 的 `themeOverrides`
  - 创建 `web/src/styles/animations.css`：淡入、选项渐现、loading 旋转
  - 更新所有组件使用 CSS 变量

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-design`, `karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 13, 14)
  - **Blocks**: None
  - **Blocked By**: Tasks 8, 9, 10, 11

  **References**:
  - **Pattern**: tech doc §1.1 样式方案 — CSS 变量 + 水墨古风主题

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: 主题一致性
    Tool: Playwright
    Steps:
      1. 截图各页面
      2. 验证背景色为宣纸白
      3. 验证文字色为墨黑
      4. 验证主按钮色为朱砂红
    Expected: 主题一致
    Evidence: .sisyphus/evidence/task-12-theme.png
  ```

  **Commit**: YES
  - Message: `feat(web): 水墨古风主题`
  - Files: `web/src/styles/variables.css, web/src/styles/animations.css, web/src/App.vue`

- [x] 13. 移动端响应式适配

  **What to do**:
  - 创建 `web/src/styles/mobile.css`：
    - `@media (max-width: 480px)` 媒体查询
    - 触控友好：按钮最小高度 44px
    - 安全区域适配：`env(safe-area-inset-*)`
    - 叙事区域最大高度限制 + 滚动
  - 更新 GameMain 布局：状态栏固定顶部，选项固定底部，叙事区域中间滚动
  - 选项按钮竖向排列（移动端）

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-design`, `karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 12, 14)
  - **Blocks**: None
  - **Blocked By**: Task 10

  **References**:
  - **Pattern**: Oracle 建议 — 状态栏 sticky, 叙事区域固定高度+滚动, 选项固定底部

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: 移动端布局
    Tool: Playwright (375x812 viewport)
    Steps:
      1. 在 /game 页面
      2. 验证无水平滚动
      3. 验证状态栏在顶部
      4. 验证选项在底部
      5. 验证叙事区域可滚动
      6. 验证按钮最小高度 44px
    Expected: 移动端布局正常
    Evidence: .sisyphus/evidence/task-13-mobile.png
  ```

  **Commit**: YES
  - Message: `feat(web): 移动端响应式适配`
  - Files: `web/src/styles/mobile.css, web/src/views/GameMain.vue`

- [x] 14. 错误处理完善 + Loading 状态

  **What to do**:
  - 统一错误处理 composable `useErrorHandler.ts`：
    - 网络错误 → "天机紊乱，连接中断" + 重试按钮
    - 404 → "轮回重启" → 返回标题页
    - 500 → "天道波动，请稍后再试" + 重试
    - 超时(>10s) → "天机推演异常" + 回标题
    - 3 次连续失败 → 建议回标题页
  - Loading 状态优化：
    - 最小展示时间 800ms（防缓存事件闪烁）
    - LoadingOverlay 使用 Naive UI NSpinner + 文案

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 12, 13)
  - **Blocks**: None
  - **Blocked By**: Task 10

  **References**:
  - **Pattern**: Oracle 建议 — 错误状态矩阵、最小加载时间、重试不丢上下文

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: 404 处理
    Tool: Playwright
    Steps:
      1. 游戏中途停止后端
      2. 触发事件获取
      3. 验证错误提示出现
      4. 验证有重试或返回标题选项
    Expected: 错误不崩溃
    Evidence: .sisyphus/evidence/task-14-error.txt
  ```

  **Commit**: YES
  - Message: `feat(web): 错误处理完善 + Loading 状态`
  - Files: `web/src/composables/useErrorHandler.ts, web/src/components/LoadingOverlay.vue`

- [x] 15. Vitest 单元测试

  **What to do**:
  - 创建 `web/vitest.config.ts`
  - `web/src/core/__tests__/normalize.test.ts`：测试 normalizeFromPydantic + normalizeFromDict
  - `web/src/core/__tests__/talents.test.ts`：测试 drawCards + getGradeColor
  - `web/src/composables/__tests__/useTypewriter.test.ts`：测试打字机逻辑（mock rAF）
  - `web/src/api/__tests__/game.test.ts`：测试 API 函数（mock fetch）
  - 配置 `pnpm test:unit` 脚本

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 5 (with Tasks 16, 17)
  - **Blocks**: None
  - **Blocked By**: Tasks 3, 7

  **References**:
  - **Pattern**: Oracle 建议 — P0: core/ 纯函数测试，P1: composable 状态机测试

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: 单元测试通过
    Tool: Bash
    Steps:
      1. cd web && pnpm test:unit
      2. 所有测试通过
    Expected: 0 failures
    Evidence: .sisyphus/evidence/task-15-unit-tests.txt
  ```

  **Commit**: YES
  - Message: `test(web): Vitest 单元测试`
  - Files: `web/vitest.config.ts, web/src/**/__tests__/*.test.ts`

- [x] 16. Playwright E2E — 完整游戏流程

  **What to do**:
  - 创建 `web/e2e/` 目录
  - `web/e2e/full-game.spec.ts`：
    - 完整游戏流程：标题 → 天赋选择 → 3 次事件循环 → 结算
    - 移动端视口测试（375x812）
  - `web/e2e/error-handling.spec.ts`：
    - 后端关闭时的错误恢复
  - 配置 `pnpm test:e2e` 脚本
  - 配置 `web/playwright.config.ts`

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: [`karpathy-guidelines`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 5 (after all previous)
  - **Blocks**: Task 17
  - **Blocked By**: All previous tasks

  **References**:
  - **Pattern**: Oracle 建议 — P2: E2E 3 个关键路径（happy path + error + mobile）

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: E2E 测试通过
    Tool: Bash
    Steps:
      1. 启动后端（uv run uvicorn）
      2. cd web && pnpm test:e2e
      3. 所有 E2E 测试通过
    Expected: 0 failures
    Evidence: .sisyphus/evidence/task-16-e2e.txt
  ```

  **Commit**: YES
  - Message: `test(web): Playwright E2E 完整游戏流程`
  - Files: `web/e2e/*.spec.ts, web/playwright.config.ts`

- [x] 17. 后端联调 + 修复

  **What to do**:
  - 启动后端 + 前端，运行完整游戏流程
  - 修复联调中发现的问题（状态格式差异、字段映射等）
  - 确保 fallback 模式（后端 AI mock）前端仍可正常游戏
  - 验证所有 4 个页面端到端流程

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`karpathy-guidelines`, `webapp-testing`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 5 (after Task 16)
  - **Blocks**: Final Wave
  - **Blocked By**: Task 16

  **References**:
  - **Pattern**: 后端 6 API 端点 — 联调时逐个验证

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: 完整联调
    Tool: Playwright
    Steps:
      1. 启动后端（mock AI 模式）
      2. 启动前端
      3. 完成一整局游戏（标题→天赋→事件→结算）
      4. 验证所有页面无报错
    Expected: 端到端流程完整
    Evidence: .sisyphus/evidence/task-17-integration.txt
  ```

  **Commit**: YES
  - Message: `fix(web): 后端联调修复`
  - Files: 按需

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.

- [x] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, run command). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in .sisyphus/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [x] F2. **Code Quality Review** — `unspecified-high`
  Run `pnpm build` + `pnpm lint` + `pnpm test:unit`. Review all changed files for: `any` type, empty catches, console.log in prod, commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, generic names.
  Output: `Build [PASS/FAIL] | Lint [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [x] F3. **Real Manual QA** — `unspecified-high` (+ `playwright` skill)
  Start from clean state (`pnpm dev` + backend `uv run uvicorn`). Execute EVERY QA scenario from EVERY task — follow exact steps, capture evidence. Play through 3 complete games. Test edge cases: network error, session expired, mobile viewport. Save to `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [x] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff (git log/diff). Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance. Detect cross-task contamination. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **1**: `feat(web): 初始化 Vue3+Vite+TS+NaiveUI 前端项目`
- **2**: `feat(web): TypeScript 类型定义 — 双状态格式 + 统一 GameState`
- **3**: `feat(web): API 客户端 + normalizeState + 错误处理`
- **4**: `feat(web): Vue Router + 4 路由 + 导航守卫`
- **5**: `feat(web): 天赋卡静态数据 + 品级抽卡逻辑`
- **6**: `feat(web): useGameState composable`
- **7**: `feat(web): useTypewriter composable — rAF 打字机效果`
- **8**: `feat(web): TitleScreen 标题画面`
- **9**: `feat(web): TalentSelect 天赋选择 + 属性分配`
- **10**: `feat(web): GameMain 事件循环核心`
- **11**: `feat(web): GameOver 结算评分`
- **12**: `feat(web): 水墨古风主题`
- **13**: `feat(web): 移动端响应式适配`
- **14**: `feat(web): 错误处理完善 + Loading 状态`
- **15**: `test(web): Vitest 单元测试`
- **16**: `test(web): Playwright E2E 完整游戏流程`
- **17**: `fix(web): 后端联调修复`

---

## Success Criteria

### Verification Commands
```bash
cd web && pnpm dev          # Expected: Vite dev server starts, no errors
cd web && pnpm build        # Expected: Build succeeds, no type errors
cd web && pnpm test:unit    # Expected: All unit tests pass
cd web && pnpm test:e2e     # Expected: E2E test passes (requires backend running)
```

### Final Checklist
- [x] 完整游戏循环可通过 UI 端到端走通
- [x] 移动端 375px 无水平滚动
- [x] 后端 fallback 时前端仍可正常游戏
- [x] 网络错误不白屏
- [x] 所有 "Must NOT Have" 项均未出现
