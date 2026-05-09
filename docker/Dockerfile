# ============================================================
# 修仙人生模拟器 — Docker 镜像
# 多阶段构建: Node 构建前端 → Python 运行后端
# ============================================================

# --------------- Stage 1: 前端构建 ---------------
FROM node:22-bookworm-slim AS frontend-builder

WORKDIR /app/web

# 安装全部依赖（构建需要 vite/vue-tsc 等 devDependencies）
COPY web/package.json web/package-lock.json ./
RUN npm install

# 复制前端源码并构建
COPY web/ ./
RUN npx vite build

# --------------- Stage 2: 后端运行 ---------------
FROM python:3.11-slim-bookworm

WORKDIR /app

# 安装 uv 包管理器
RUN pip install --no-cache-dir uv

# 复制 Python 依赖文件
COPY pyproject.toml uv.lock ./

# 安装 Python 依赖（不包含开发依赖）
RUN uv sync --frozen --no-dev

# 复制后端源码
COPY app/ ./app/
COPY schema.sql ./

# 复制前端构建产物
COPY --from=frontend-builder /app/web/dist ./web/dist

# 创建数据库持久化目录（与游戏静态数据分离）
RUN mkdir -p /app/data

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 启动后端服务（使用已构建的 venv，避免运行时重新下载依赖）
CMD [".venv/bin/python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
