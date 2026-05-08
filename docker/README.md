# Docker 部署指南

## 快速启动

```bash
# 1. 在项目根目录创建 .env 文件
cp .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key:
# DEEPSEEK_API_KEY=sk-your-real-key

# 2. 启动服务
docker compose -f docker/docker-compose.yml up -d

# 3. 访问
# http://localhost:8000
```

## 镜像构建

```bash
# 在项目根目录执行
docker build -f docker/Dockerfile -t random-story:latest .
```

## 配置说明

所有配置通过环境变量注入，支持以下变量：

| 变量                | 默认值                         | 说明               |
| ------------------- | ------------------------------ | ------------------ |
| `DEEPSEEK_API_KEY`   | (必填)                         | DeepSeek API 密钥   |
| `DEEPSEEK_MODEL`     | `deepseek-v4-flash`            | 使用的模型          |
| `DEEPSEEK_BASE_URL`  | `https://api.deepseek.com`     | API 基础地址        |
| `DATABASE_PATH`      | `/app/app/data/game.db`        | SQLite 数据库路径   |
| `CORS_ORIGINS`       | `*`                            | 允许的跨域来源      |
| `MAX_EVENTS_PER_GAME` | `60`                          | 每局最大事件数      |
| `CACHE_TTL`          | `1800`                         | AI 缓存 TTL（秒）  |

## 数据持久化

SQLite 数据库文件挂载到宿主机的 `data/` 目录，容器重启不会丢失游戏数据。
