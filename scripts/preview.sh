#!/usr/bin/env bash
# ==============================================================================
# ZgAdmin — 预览脚本
# 用法: ./scripts/preview.sh
# 说明: 前端运行在 8686 端口，后端使用 SQLite 数据库（零配置即用）
# ==============================================================================
set -euo pipefail
export UV_LINK_MODE=copy

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
ENV_FILE="$PROJECT_ROOT/.env"
ENV_EXAMPLE="$PROJECT_ROOT/.env.example"

BACKEND_HOST="0.0.0.0"
BACKEND_PORT="7001"
FRONTEND_PORT="8686"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_step()  { echo -e "${BLUE}[STEP]${NC}  $*"; }
banner()    { echo -e "${BOLD}$*${NC}"; }

BACKEND_PID=""
FRONTEND_PID=""

# ──────────────────────── 环境检查 ────────────────────────────────────────────
check_deps() {
    local missing=()

    command -v python3 &>/dev/null || missing+=("python3 (>=3.13)")
    command -v uv       &>/dev/null || missing+=("uv       — pip install uv 或 https://docs.astral.sh/uv/")
    command -v bun      &>/dev/null || missing+=("bun      — curl -fsSL https://bun.sh/install | bash")

    if [ ${#missing[@]} -gt 0 ]; then
        log_error "缺少运行时依赖:"
        for m in "${missing[@]}"; do echo "         $m"; done
        exit 1
    fi
}

# ──────────────────────── 初始化 .env（仅预览用） ──────────────────────────────
prepare_env() {
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f "$ENV_EXAMPLE" ]; then
            cp "$ENV_EXAMPLE" "$ENV_FILE"
            log_info "已从 .env.example 创建 .env"
        else
            log_error "缺少 .env.example 模板文件"
            exit 1
        fi
    fi
}

port_in_use() {
    local port="$1"
    lsof -i :"$port" -sTCP:LISTEN -t &>/dev/null || ss -tlnp 2>/dev/null | grep -q ":${port} "
}

release_port() {
    local port="$1"
    if ! port_in_use "$port"; then return 0; fi
    log_warn "端口 $port 已被占用，正在释放..."
    local pids
    pids=$(lsof -ti :"$port" -sTCP:LISTEN 2>/dev/null)
    for pid in $pids; do
        kill "$pid" 2>/dev/null
    done
    sleep 1
    for pid in $pids; do
        kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null
    done
}

cleanup() {
    echo ""
    log_warn "正在停止服务..."
    [ -n "$BACKEND_PID" ]  && kill "$BACKEND_PID"  2>/dev/null && wait "$BACKEND_PID"  2>/dev/null || true
    [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null && wait "$FRONTEND_PID" 2>/dev/null || true
    pids=$(lsof -ti :"$BACKEND_PORT" -sTCP:LISTEN 2>/dev/null) && kill $pids 2>/dev/null || true
    pids=$(lsof -ti :"$FRONTEND_PORT" -sTCP:LISTEN 2>/dev/null) && kill $pids 2>/dev/null || true
    log_info "所有服务已停止"
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# ──────────────────────── 后端（SQLite） ──────────────────────────────────────
run_backend() {
    banner "═══════════════════════════════════════════════════════════════"
    banner "  ZgAdmin 后端 (SQLite)  http://localhost:${BACKEND_PORT}"
    banner "═══════════════════════════════════════════════════════════════"
    release_port "$BACKEND_PORT"
    log_step "安装后端依赖..."
    cd "$BACKEND_DIR"
    uv sync --no-dev --quiet 2>&1 | tail -3
    log_step "启动后端 (SQLite, 端口 $BACKEND_PORT)..."
    DB_SCHEME=sqlite \
    FRONTEND_HOST=http://localhost:${FRONTEND_PORT} \
    BACKEND_CORS_ORIGINS="http://localhost,http://localhost:${FRONTEND_PORT}" \
    RELOAD=false \
    PYTHONUNBUFFERED=1 \
    uv run python main.py &
    BACKEND_PID=$!
}

# ──────────────────────── 前端（8686 端口） ────────────────────────────────────
run_frontend() {
    banner "═══════════════════════════════════════════════════════════════"
    banner "  ZgAdmin 前端 (Vue 3 + Vite)  http://localhost:${FRONTEND_PORT}"
    banner "═══════════════════════════════════════════════════════════════"
    release_port "$FRONTEND_PORT"
    log_step "安装前端依赖..."
    cd "$FRONTEND_DIR"
    bun install --silent 2>&1 | tail -3
    log_step "启动前端 (端口 $FRONTEND_PORT)..."
    VITE_PORT=$FRONTEND_PORT bun dev &
    FRONTEND_PID=$!
}

# ──────────────────────── 主入口 ──────────────────────────────────────────────
main() {
    cd "$PROJECT_ROOT"
    check_deps
    prepare_env

    run_backend
    run_frontend

    echo ""
    banner "═══════════════════════════════════════════════════════════════"
    banner "  ZgAdmin 预览模式已启动"
    banner "═══════════════════════════════════════════════════════════════"
    echo ""
    echo -e "  前端: ${GREEN}http://localhost:${FRONTEND_PORT}${NC}"
    echo -e "  后端: ${GREEN}http://localhost:${BACKEND_PORT}${NC}"
    echo -e "  API:  ${GREEN}http://localhost:${BACKEND_PORT}/api/v1/docs${NC}"
    echo ""
    echo -e "  数据库: ${YELLOW}SQLite${NC}"
    echo -e "  默认管理员: admin / admin123456"
    echo -e "  按 ${YELLOW}Ctrl+C${NC} 停止"
    echo ""

    wait -n 2>/dev/null || wait
    log_error "某个服务已退出"
}

main "$@"
