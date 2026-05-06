#!/usr/bin/env bash
# ==============================================================================
# PyTool 启动脚本 — 前后端并行运行，日志直接输出到终端
# 用法: ./start.sh [dev|backend|frontend|stop|status]
# ==============================================================================

set -euo pipefail

# 云开发环境通常不支持硬链接，直接复制避免警告
export UV_LINK_MODE=copy

# ----------------------------- 常量 -------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
ENV_FILE="$PROJECT_ROOT/.env"

BACKEND_HOST="0.0.0.0"
BACKEND_PORT="7001"
FRONTEND_PORT="7000"

# ----------------------------- 颜色 -------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'
BOLD='\033[1m'; NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_step()  { echo -e "${BLUE}[STEP]${NC}  $*"; }
banner()    { echo -e "${BOLD}$*${NC}"; }

# 进程 PID，用于 trap 清理
BACKEND_PID=""
FRONTEND_PID=""

# ----------------------------- 工具函数 ----------------------------------------
load_env() {
    if [ -f "$ENV_FILE" ]; then
        while IFS='=' read -r key value; do
            key=$(echo "$key" | xargs)
            value=$(echo "$value" | xargs | sed 's/^"//;s/"$//')
            case "$key" in
                PORT)     BACKEND_PORT="${value:-$BACKEND_PORT}" ;;
                HOST)     BACKEND_HOST="${value:-$BACKEND_HOST}" ;;
                VITE_PORT) FRONTEND_PORT="${value:-$FRONTEND_PORT}" ;;
            esac
        done < <(grep -v '^\s*#' "$ENV_FILE" | grep '=' || true)
    fi
}

port_in_use() {
    local port="$1"
    lsof -i :"$port" -sTCP:LISTEN -t &>/dev/null || \
        ss -tlnp 2>/dev/null | grep -q ":${port} "
}

release_port() {
    local port="$1"
    if ! port_in_use "$port"; then return 0; fi
    log_warn "端口 $port 已被占用，正在释放..."
    local pids
    pids=$(lsof -ti :"$port" -sTCP:LISTEN 2>/dev/null)
    for pid in $pids; do
        kill "$pid" 2>/dev/null && log_info "已终止 PID $pid (端口 $port)"
    done
    sleep 1
    for pid in $pids; do
        kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null
    done
    if port_in_use "$port"; then
        log_error "端口 $port 释放失败，请手动处理"
        return 1
    fi
    log_info "端口 $port 已释放"
}

cleanup() {
    echo ""
    log_warn "正在停止服务..."
    [ -n "$BACKEND_PID" ]  && kill "$BACKEND_PID"  2>/dev/null && wait "$BACKEND_PID"  2>/dev/null || true
    [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null && wait "$FRONTEND_PID" 2>/dev/null || true
    # 兜底：按端口清理残留
    pids=$(lsof -ti :"$BACKEND_PORT" -sTCP:LISTEN 2>/dev/null) && kill $pids 2>/dev/null || true
    pids=$(lsof -ti :"$FRONTEND_PORT" -sTCP:LISTEN 2>/dev/null) && kill $pids 2>/dev/null || true
    log_info "所有服务已停止"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# ----------------------------- 后端启动 ----------------------------------------
run_backend() {
    banner "═══════════════════════════════════════════════════════════════"
    banner "  PyTool 后端 (FastAPI) — http://localhost:${BACKEND_PORT}"
    banner "═══════════════════════════════════════════════════════════════"

    release_port "$BACKEND_PORT"

    log_step "安装后端依赖..."
    cd "$BACKEND_DIR"
    UV_LINK_MODE=copy uv sync --no-dev --quiet 2>&1 | tail -3

    log_step "启动后端 (端口 $BACKEND_PORT)..."
    PYTHONUNBUFFERED=1 uv run python main.py &
    BACKEND_PID=$!
}

# ----------------------------- 前端启动 ----------------------------------------
run_frontend() {
    banner "═══════════════════════════════════════════════════════════════"
    banner "  PyTool 前端 (Vue 3 + Vite) — http://localhost:${FRONTEND_PORT}"
    banner "═══════════════════════════════════════════════════════════════"

    release_port "$FRONTEND_PORT"

    log_step "安装前端依赖..."
    cd "$FRONTEND_DIR"
    bun install --silent 2>&1 | tail -3

    log_step "启动前端 (端口 $FRONTEND_PORT)..."
    bun dev &
    FRONTEND_PID=$!
}

# ----------------------------- 状态 -------------------------------------------
show_status() {
    banner "PyTool 服务状态"
    echo ""

    if port_in_use "$BACKEND_PORT"; then
        echo -e "  ${GREEN}●${NC} 后端: 运行中 (端口 $BACKEND_PORT)"
    else
        echo -e "  ${RED}●${NC} 后端: 未运行"
    fi

    if port_in_use "$FRONTEND_PORT"; then
        echo -e "  ${GREEN}●${NC} 前端: 运行中 (端口 $FRONTEND_PORT)"
    else
        echo -e "  ${RED}●${NC} 前端: 未运行"
    fi
    echo ""
}

# ----------------------------- 帮助 -------------------------------------------
show_help() {
    echo ""
    banner "PyTool 启动脚本"
    echo ""
    echo "用法: ./start.sh [命令]"
    echo ""
    echo "命令:"
    echo "  dev        启动前后端（默认）"
    echo "  backend    仅启动后端"
    echo "  frontend   仅启动前端"
    echo "  stop       停止所有服务"
    echo "  status     查看运行状态"
    echo "  help       帮助信息"
    echo ""
}

# ----------------------------- 主流程 -----------------------------------------
main() {
    local cmd="${1:-dev}"

    cd "$PROJECT_ROOT"
    load_env

    case "$cmd" in
        dev)
            run_backend
            run_frontend
            echo ""
            banner "═══════════════════════════════════════════════════════════════"
            banner "  PyTool 开发服务已启动"
            banner "═══════════════════════════════════════════════════════════════"
            echo ""
            echo -e "  前端: ${GREEN}http://localhost:${FRONTEND_PORT}${NC}"
            echo -e "  后端: ${GREEN}http://localhost:${BACKEND_PORT}${NC}"
            echo -e "  API:  ${GREEN}http://localhost:${BACKEND_PORT}/api/v1/docs${NC}"
            echo ""
            echo -e "  按 ${YELLOW}Ctrl+C${NC} 停止所有服务"
            echo ""
            # 等待任意子进程退出
            wait -n 2>/dev/null || wait
            log_error "某个服务已退出"
            ;;
        backend)
            run_backend
            echo ""
            log_info "后端运行中，按 Ctrl+C 停止..."
            wait "$BACKEND_PID"
            ;;
        frontend)
            run_frontend
            echo ""
            log_info "前端运行中，按 Ctrl+C 停止..."
            wait "$FRONTEND_PID"
            ;;
        stop)
            # trap cleanup 已注册，exit 会触发清理
            log_info "正在通过端口清理..."
            release_port "$BACKEND_PORT"
            release_port "$FRONTEND_PORT"
            log_info "已停止"
            trap - EXIT  # 取消 trap，避免 cleanup 重复执行
            ;;
        status)
            show_status
            trap - EXIT
            ;;
        help|--help|-h)
            show_help
            trap - EXIT
            ;;
        *)
            log_error "未知命令: $cmd"
            show_help
            trap - EXIT
            exit 1
            ;;
    esac
}

main "$@"
