# 重生模拟器 前端 MVP — Handoff 报告

## 项目概览

| 项目 | 值 |
|------|-----|
| 项目目录 | `/Users/haochen/developer/private_project/random_story/web/` |
| 技术栈 | Vue3 + Vite + TypeScript + Naive UI |
| 状态 | **完成** — 17/17 任务，所有测试通过 |
| 计划 | `.sisyphus/plans/rebirth-frontend-mvp.md` |
| 证据 | `.sisyphus/evidence/` |

## 交付物清单

### 项目结构
```
web/
├── src/
│   ├── api/           # API 客户端 (client.ts, game.ts)
│   ├── components/    # UI 组件 (6 个)
│   ├── composables/   # 可组合函数 (4 个)
│   ├── core/          # 核心逻辑 (types.ts, normalize.ts, talents.ts)
│   ├── data/          # 静态数据 (talents.ts - 20 张卡)
│   ├── styles/        # 样式 (variables.css, animations.css, mobile.css, theme.ts)
│   └── views/         # 4 个页面视图
├── e2e/               # Playwright E2E 测试
└── vitest.config.ts   # Vitest 配置
```

### 页面视图
1. **TitleScreen** — 标题 "重生模拟器" + "开始修仙" 按钮 + 排行榜(空)
2. **TalentSelect** — 三步：角色名/性别 → 抽3张天赋卡 → 10点属性分配
3. **GameMain** — 状态机事件循环 (fetching→typing→choosing→submitting→aftermath→gameover)
4. **GameOver** — 结局展示 + 评分/等级 + 再来一局

### API 集成 (6 端点)
- `POST /api/v1/game/start` — 创建游戏 → NormalizedGameState
- `POST /api/v1/game/event` — 获取事件 → EventResponse
- `POST /api/v1/game/event/choose` — 选择选项 → ChooseResponse → NormalizedGameState
- `GET /api/v1/game/state/{session_id}` — 查询状态 → NormalizedGameState
- `POST /api/v1/game/end` — 结算 → EndGameResponse
- `GET /api/v1/game/leaderboard` — 排行榜 → LeaderboardEntry[]

### 双状态格式统一
- `PlayerStatePydantic` → `normalizeFromPydantic()` → `NormalizedGameState`
- `GameStateDict` → `normalizeFromDict()` → `NormalizedGameState`

## 测试结果

| 测试类型 | 结果 |
|---------|------|
| Vitest 单元测试 | 4 files, 13 tests — **全部通过** |
| Playwright E2E | 5 tests — **全部通过** |
| 后端 API 集成 | 6 端点全部验证通过 |
| pnpm build | **成功** (无类型错误) |

## 验证命令

```bash
cd web && pnpm dev          # 开发服务器 :5173
cd web && pnpm build        # 生产构建
cd web && pnpm test:unit    # 单元测试
cd web && pnpm test:e2e     # E2E 测试 (需先启动后端)
```

## 关键决策回顾

| 决策 | 方案 | 原因 |
|------|------|------|
| 状态管理 | `ref()` 模块单例 | 简单够用，不需要 Pinia |
| 天赋数据 | 前端内嵌 20 张卡 | 后端无天赋 API |
| 打字机 | requestAnimationFrame | 后台暂停、省电、同步渲染 |
| 路由守卫 | sessionStorage 检查 | 防止直接访问 /game |
| 错误处理 | FetchError + 中文提示 | 用户友好不白屏 |
| 主题 | CSS 变量 + Naive UI overrides | 水墨古风 |

## DIFF 摘要

```
17 commits:
  feat(web): 初始化 Vue3+Vite+TS+NaiveUI 前端项目
  feat(web): TypeScript 类型定义 — 双状态格式 + 统一 GameState
  feat(web): API 客户端 + normalizeState + 错误处理
  feat(web): Vue Router + 4 路由 + 导航守卫
  feat(web): 天赋卡静态数据 + 品级抽卡逻辑
  feat(web): useGameState composable
  feat(web): useTypewriter composable — rAF 打字机效果
  feat(web): TitleScreen 标题画面
  feat(web): TalentSelect 天赋选择 + 属性分配
  feat(web): GameMain 事件循环核心
  feat(web): GameOver 结算评分
  feat(web): 水墨古风主题 — CSS 变量 + Naive UI 覆盖
  feat(web): 移动端响应式适配
  feat(web): 错误处理完善 + Loading 状态
  test(web): Vitest 单元测试
  test(web): Playwright E2E — 标题页/天赋选择/移动端
  fix(web): 后端联调修复 — 全流程集成测试
```

## Must NOT Have (已保留)
- ❌ 后端代码修改 ✓
- ❌ Pinia ✓ (用 ref 模块单例)
- ❌ Canvas/WebGL ✓
- ❌ HP/Qi 进度条 ✓
- ❌ 天赋数值展示 ✓
- ❌ 突破系统 UI ✓
- ❌ i18n/音效/暗色模式 ✓

## 遗留问题
- GameMain 页面需要后端运行时才能完整展示 (fallback 叙事)
- 排行榜始终返回空数组 (后端无数据库)
- 风格评分等级未从后端直接展示 (通过 endGame API 获取)
