# 🏔️ 修仙人生模拟器

> **AI 驱动的修仙题材文字冒险游戏。** 没有战斗动画、没有地图探索——你的人生就是你的游戏。选择天赋、分配属性，AI 为你生成独一无二的修仙人生叙事。每次选择都有后果，每次突破都攸关生死。

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.5-4FC08D.svg)](https://vuejs.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 🎮 游戏特色

| 机制     | 说明                                                              |
| -------- | ----------------------------------------------------------------- |
| **境界**     | 9 级：凡人 → 炼气 → 筑基 → 金丹 → 元婴 → 化神 → 合体 → 大乘 → 渡劫飞升 |
| **突破**     | **高风险高回报**：成功=升境界，失败=修为归零/受伤/折寿。可用丹药提高成功率    |
| **天赋**     | 开局抽卡选 3 张，影响突破概率、修炼速度和事件权重。0.5% 出绝世天赋     |
| **属性**     | 四维可分配：根骨、悟性、心境、福缘，各影响不同方面                         |
| **事件**     | AI 根据 76 个模板动态生成叙事，每次选择都有后果                              |
| **寿命**     | 时间有限，境界越高寿元越长。最终目标是飞升前不死                              |

### 玩家旅程

```
创建角色 → 天赋抽卡 → 分配属性 → 进入主循环
                                      ↓
                               获取事件（AI 生成叙事）
                                      ↓
                                 有选项？→ 是 → 选择 → 计算后果
                                      ↓                    ↓
                                     否 → 安静年            ↓
                                      ↓                    ↓
                              突破条件满足？                ↓
                                  ↓         ↓              ↓
                                  是 → 突破事件             ↓
                                  ↓   成功/失败              ↓
                                  ↓                         ↓
                              循环直到死亡或飞升 → 结算评分
```

---

## 🚀 快速开始（Docker）

```bash
# 1. 克隆项目
git clone git@github.com:a414338069/random_story.git
cd random_story

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key

# 3. 启动
docker compose -f docker/docker-compose.yml up -d

# 4. 访问 http://localhost:8000
```

---

## 🛠️ 技术栈

| 维度 | 技术 |
| ---- | ---- |
| 后端 | **FastAPI** + Python ≥3.11 + SQLite + uv |
| 前端 | **Vue 3** + NaiveUI + TypeScript + Vite |
| AI   | **DeepSeek API** 生成叙事和选项 |
| 测试 | pytest + pytest-asyncio（后端）/ Vitest + Playwright（前端） |

---

## 📖 开发指南

### 环境要求
- Python ≥ 3.11
- Node.js ≥ 22
- [uv](https://docs.astral.sh/uv/)（Python 包管理器）

### 本地开发

```bash
# 后端
uv sync                         # 安装依赖
uv run uvicorn app.main:app --reload --port 8000

# 前端（新终端）
cd web
npm install
npm run dev                     # http://localhost:5173

# 运行测试
uv run pytest                   # 后端测试
cd web && npm run test:unit     # 前端单元测试
```

### 项目结构

```
random_story/
├── app/                    # 后端 (FastAPI)
│   ├── main.py             # 应用入口
│   ├── config.py           # 配置管理
│   ├── models/             # Pydantic 模型
│   ├── routers/            # API 路由
│   ├── services/           # 核心服务层
│   │   ├── game_service.py     # 游戏编排
│   │   ├── event_engine.py     # 事件引擎
│   │   ├── ai_service.py       # DeepSeek 集成
│   │   ├── breakthrough.py     # 突破系统
│   │   └── ...
│   └── data/               # 游戏数据
│       ├── realms.yaml     # 境界配置
│       ├── talents.yaml    # 天赋配置
│       └── events/         # 76 个事件模板
├── web/                    # 前端 (Vue 3)
│   └── src/
│       ├── views/          # 页面视图
│       ├── components/     # UI 组件
│       ├── composables/    # 组合式函数
│       └── api/            # API 客户端
├── docker/                 # Docker 部署配置
├── tests/                  # 测试
└── pyproject.toml          # Python 项目配置
```

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request。目前项目处于 MVP 阶段，主要方向：

- [x] 核心游戏循环
- [x] 突破系统
- [x] AI 叙事生成
- [x] Docker 部署
- [ ] 存档系统完善
- [ ] 移动端适配
- [ ] 性能优化

---

## 📄 License

MIT License
