#!/usr/bin/env bash
# ==============================================================================
# ZgAdmin — Docker 生产环境入口脚本
# 职责：启动 nginx（前端）+ FastAPI 后端，管理进程生命周期与信号
# ==============================================================================
set -eo pipefail

# ── 信号处理：优雅关闭 ────────────────────────────────────────────────────────
NGINX_PID=""
BACKEND_PID=""
STOPPING=false

shutdown() {
    if [ "$STOPPING" = true ]; then return; fi
    STOPPING=true
    echo "[ENTRYPOINT] 正在停止服务..."

    if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo "[ENTRYPOINT] 发送 SIGTERM 给后端 (PID: $BACKEND_PID)..."
        kill -TERM "$BACKEND_PID" 2>/dev/null || true
        wait "$BACKEND_PID" 2>/dev/null || true
    fi

    if [ -n "$NGINX_PID" ] && kill -0 "$NGINX_PID" 2>/dev/null; then
        echo "[ENTRYPOINT] 发送 SIGTERM 给 nginx (PID: $NGINX_PID)..."
        kill -TERM "$NGINX_PID" 2>/dev/null || true
        wait "$NGINX_PID" 2>/dev/null || true
    fi

    echo "[ENTRYPOINT] 所有服务已停止"
    exit 0
}

trap shutdown SIGTERM SIGINT SIGQUIT

# ── 启动 nginx（前端） ─────────────────────────────────────────────────────────
echo "[ENTRYPOINT] 启动 nginx..."
nginx -g "daemon off;" &
NGINX_PID=$!

# 等待 nginx 就绪
RETRIES=0
MAX_RETRIES=30
while ! python3 -c "import urllib.request; urllib.request.urlopen('http://localhost/')" 2>/dev/null; do
    RETRIES=$((RETRIES + 1))
    if [ "$RETRIES" -ge "$MAX_RETRIES" ]; then
        echo "[ENTRYPOINT] nginx 启动超时，退出"
        exit 1
    fi
    sleep 0.5
done
echo "[ENTRYPOINT] nginx 已就绪"

# ── 启动后端 ───────────────────────────────────────────────────────────────────
echo "[ENTRYPOINT] 启动后端..."
cd /backend
uv run main.py &
BACKEND_PID=$!

# 等待后端就绪
RETRIES=0
while ! python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:7001/api/v1/base/health')" 2>/dev/null; do
    RETRIES=$((RETRIES + 1))
    if [ "$RETRIES" -ge "$MAX_RETRIES" ]; then
        echo "[ENTRYPOINT] 后端启动超时，退出"
        kill -TERM "$NGINX_PID" 2>/dev/null || true
        exit 1
    fi
    sleep 1
done
echo "[ENTRYPOINT] 后端已就绪"

echo "[ENTRYPOINT] =============================="
echo "[ENTRYPOINT] ZgAdmin 已启动"
echo "[ENTRYPOINT] 前端: http://localhost"
echo "[ENTRYPOINT] 后端: http://localhost:7001"
echo "[ENTRYPOINT] =============================="

# ── 进程监控 ───────────────────────────────────────────────────────────────────
# 事件驱动：任一子进程退出立即感知，区分退出进程
wait -n "$NGINX_PID" "$BACKEND_PID" 2>/dev/null
if ! kill -0 "$NGINX_PID" 2>/dev/null; then
    echo "[ENTRYPOINT] nginx 意外退出"
elif ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "[ENTRYPOINT] 后端意外退出"
fi
shutdown
exit 1
