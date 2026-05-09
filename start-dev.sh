#!/usr/bin/env bash
# ============================================================
# 修仙人生模拟器 — 开发环境一键启动/重启脚本
# 用法: ./start-dev.sh
# 功能: 检测端口占用 → kill 旧进程 → 启动后端(8000) + 前端(5173)
# ============================================================

set -e

BACKEND_PORT=8000
FRONTEND_PORT=5173
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# --------------- 颜色 ---------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}════════════════════════════════════════${NC}"
echo -e "${CYAN}  修仙人生模拟器 — 开发环境启动${NC}"
echo -e "${CYAN}════════════════════════════════════════${NC}"

# --------------- 1. 杀掉占用端口的旧进程 ---------------
kill_port() {
    local port=$1
    local pids
    pids=$(lsof -ti:"$port" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo -e "${YELLOW}[端口:${port}] 检测到旧进程，正在终止...${NC}"
        for pid in $pids; do
            kill "$pid" 2>/dev/null || true
        done
        sleep 1
        # 二次确认，强制杀掉
        pids=$(lsof -ti:"$port" 2>/dev/null || true)
        if [ -n "$pids" ]; then
            echo -e "${YELLOW}[端口:${port}] 强制终止顽固进程...${NC}"
            for pid in $pids; do
                kill -9 "$pid" 2>/dev/null || true
            done
            sleep 1
        fi
        echo -e "${GREEN}[端口:${port}] 旧进程已终止${NC}"
    else
        echo -e "${GREEN}[端口:${port}] 空闲${NC}"
    fi
}

kill_port "$BACKEND_PORT"
kill_port "$FRONTEND_PORT"

# --------------- 2. 启动后端 ---------------
echo ""
echo -e "${CYAN}▶ 启动后端 (FastAPI + uvicorn, port ${BACKEND_PORT})${NC}"
cd "$PROJECT_DIR"
nohup uv run uvicorn app.main:app --reload --port "$BACKEND_PORT" \
    > /tmp/random-story-backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}  后端 PID: ${BACKEND_PID}${NC}"
echo -e "  日志: /tmp/random-story-backend.log"

# 等待后端就绪（绕过系统代理）
echo -n "  等待后端就绪"
for i in $(seq 1 30); do
    if curl -s --noproxy '*' -o /dev/null -w "%{http_code}" "http://127.0.0.1:${BACKEND_PORT}/docs" 2>/dev/null | grep -q "200"; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
    echo -n "."
    sleep 1
done
echo ""

# --------------- 3. 启动前端 ---------------
echo -e "${CYAN}▶ 启动前端 (Vite + Vue3, port ${FRONTEND_PORT})${NC}"
cd "$PROJECT_DIR/web"
nohup npm run dev -- --port "$FRONTEND_PORT" \
    > /tmp/random-story-frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}  前端 PID: ${FRONTEND_PID}${NC}"
echo -e "  日志: /tmp/random-story-frontend.log"

# 等待前端就绪（绕过系统代理，Vite 可能只监听 IPv6）
echo -n "  等待前端就绪"
for i in $(seq 1 15); do
    if lsof -ti:"${FRONTEND_PORT}" > /dev/null 2>&1; then
        echo -e " ${GREEN}✓${NC} (端口已监听)"
        break
    fi
    echo -n "."
    sleep 1
done
echo ""

# --------------- 4. 完成 ---------------
echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  全栈开发环境启动完成！${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "  ${CYAN}后端:${NC} http://localhost:${BACKEND_PORT}/docs"
echo -e "  ${CYAN}前端:${NC} http://localhost:${FRONTEND_PORT}"
echo ""
echo -e "  ${YELLOW}停止服务:${NC} ./start-dev.sh 再次运行会自动重启"
echo -e "  ${YELLOW}查看后端日志:${NC} tail -f /tmp/random-story-backend.log"
echo -e "  ${YELLOW}查看前端日志:${NC} tail -f /tmp/random-story-frontend.log"
echo ""
