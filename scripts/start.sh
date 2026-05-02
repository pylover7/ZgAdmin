#!/usr/bin/env bash
# ==============================================================================
# PyTool 启动脚本
# 用法: ./start.sh [dev|backend|frontend|docker|stop|status]
# ==============================================================================

set -euo pipefail

# ----------------------------- 配置 -------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
LOG_DIR="$PROJECT_ROOT/.logs"
PID_DIR="$PROJECT_ROOT/.pids"
ENV_FILE="$PROJECT_ROOT/.env"

# 后端默认端口（从 .env 读取，无文件则回退）
BACKEND_PORT="7001"
FRONTEND_PORT="8848"

# PID 文件路径
BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

# ----------------------------- 工具函数 ---------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'
BOLD='\033[1m'; NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_step()  { echo -e "${BLUE}[STEP]${NC}  $*"; }
banner()    { echo -e "${BOLD}$*${NC}"; }

# ----------------------------- 环境检查 ---------------------------------------
check_deps() {
    log_step "检查运行时依赖..."

    local missing=()
    command -v python3 &>/dev/null || missing+=("python3 (>=3.13)")
    command -v uv       &>/dev/null || missing+=("uv")
    command -v node     &>/dev/null || missing+=("node (>=20)")
    command -v bun      &>/dev/null || missing+=("bun")

    if [ ${#missing[@]} -gt 0 ]; then
        log_error "缺少以下依赖:"
        for m in "${missing[@]}"; do
            echo "  - $m"
        done
        exit 1
    fi
    log_info "所有依赖已就绪"
}

load_env() {
    if [ -f "$ENV_FILE" ]; then
        # 安全加载 .env，只解析 KEY=VALUE 行
        while IFS='=' read -r key value; do
            key=$(echo "$key" | xargs)
            value=$(echo "$value" | xargs)
            case "$key" in
                PORT)    BACKEND_PORT="${value:-$BACKEND_PORT}" ;;
                HOST)    BACKEND_HOST="${value:-0.0.0.0}" ;;
                DB_SCHEME) DB_SCHEME="${value:-sqlite}" ;;
                DB_SERVER) DB_SERVER="${value:-localhost}" ;;
                DB_PORT)   DB_PORT="${value:-5432}" ;;
            esac
        done < <(grep -v '^\s*#' "$ENV_FILE" | grep '=' || true)
    fi

    # 前端端口从 vite 配置默认值读取
    FRONTEND_PORT="${VITE_PORT:-8848}"
}

setup_dirs() {
    mkdir -p "$LOG_DIR" "$PID_DIR"
}

port_in_use() {
    local port="$1"
    ss -tlnp 2>/dev/null | grep -q ":${port} " || \
        lsof -i :"$port" -sTCP:LISTEN -t &>/dev/null || \
        netstat -tlnp 2>/dev/null | grep -q ":${port} "
}

kill_by_pid() {
    local pid_file="$1"
    local name="$2"
    if [ -f "$pid_file" ]; then
        local pid
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            sleep 1
            kill -9 "$pid" 2>/dev/null || true
            log_info "已停止 $name (PID: $pid)"
        fi
        rm -f "$pid_file"
    fi
}

kill_port() {
    local port="$1"
    local pids

    if ! port_in_use "$port"; then
        return 0
    fi

    pids=$(lsof -ti :"$port" -sTCP:LISTEN 2>/dev/null || \
           ss -tlnp 2>/dev/null | grep ":${port} " | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' || \
           netstat -tlnp 2>/dev/null | grep ":${port} " | awk '{print $NF}' | sed 's|/.*||')

    if [ -n "$pids" ]; then
        log_warn "端口 $port 已被占用，正在强制释放..."
        for pid in $pids; do
            kill "$pid" 2>/dev/null && log_info "已终止 PID $pid (端口 $port)"
        done
        sleep 1
        # 二次确认，顽固进程强制 kill
        for pid in $pids; do
            kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null && log_info "已强制终止 PID $pid"
        done
    fi

    if port_in_use "$port"; then
        log_error "端口 $port 强制释放失败，手动检查"
        return 1
    fi
    log_info "端口 $port 已释放"
}

# ----------------------------- 后端 -------------------------------------------
start_backend() {
    banner "═══════════════════════════════════════════════════════════════"
    banner "  启动 PyTool 后端 (FastAPI)"
    banner "═══════════════════════════════════════════════════════════════"

    kill_port "$BACKEND_PORT" || return 1

    log_step "安装后端依赖..."
    cd "$BACKEND_DIR"
    uv sync --no-dev --quiet 2>&1 | tail -3

    log_step "启动后端服务 (端口: $BACKEND_PORT)..."
    PYTHONUNBUFFERED=1 nohup uv run python main.py > "$BACKEND_LOG" 2>&1 &
    echo $! > "$BACKEND_PID_FILE"

    # 等待后端就绪
    log_step "等待后端就绪..."
    local max_wait=30
    local waited=0
    while [ $waited -lt $max_wait ]; do
        if curl -s "http://localhost:${BACKEND_PORT}/api/v1/docs" > /dev/null 2>&1; then
            log_info "后端已就绪 (http://localhost:${BACKEND_PORT})"
            log_info "API 文档: http://localhost:${BACKEND_PORT}/api/v1/docs"
            return 0
        fi
        sleep 2
        waited=$((waited + 2))
    done

    # 超时检查
    if kill -0 "$(cat "$BACKEND_PID_FILE")" 2>/dev/null; then
        log_warn "后端进程已启动但未在 ${max_wait}s 内就绪，请查看日志: $BACKEND_LOG"
    else
        log_error "后端启动失败，查看日志: $BACKEND_LOG"
        return 1
    fi
}

# ----------------------------- 前端 -------------------------------------------
start_frontend() {
    banner "═══════════════════════════════════════════════════════════════"
    banner "  启动 PyTool 前端 (Vue 3 + Vite)"
    banner "═══════════════════════════════════════════════════════════════"

    kill_port "$FRONTEND_PORT" || return 1

    log_step "安装前端依赖..."
    cd "$FRONTEND_DIR"
    bun install --silent 2>&1 | tail -3

    log_step "启动前端开发服务器 (端口: $FRONTEND_PORT)..."
    stdbuf -oL nohup bun dev > "$FRONTEND_LOG" 2>&1 &
    echo $! > "$FRONTEND_PID_FILE"

    # 等待前端就绪
    log_step "等待前端就绪..."
    local max_wait=60
    local waited=0
    while [ $waited -lt $max_wait ]; do
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:${FRONTEND_PORT}" 2>/dev/null | grep -qE "^(200|302|304)$"; then
            log_info "前端已就绪 (http://localhost:${FRONTEND_PORT})"
            return 0
        fi
        sleep 2
        waited=$((waited + 2))
    done

    if kill -0 "$(cat "$FRONTEND_PID_FILE")" 2>/dev/null; then
        log_warn "前端进程已启动但未在 ${max_wait}s 内就绪，请查看日志: $FRONTEND_LOG"
    else
        log_error "前端启动失败，查看日志: $FRONTEND_LOG"
        return 1
    fi
}

# ----------------------------- Docker -----------------------------------------
start_docker() {
    banner "═══════════════════════════════════════════════════════════════"
    banner "  启动 PyTool (Docker Compose)"
    banner "═══════════════════════════════════════════════════════════════"

    command -v docker &>/dev/null || {
        log_error "未安装 Docker"; exit 1;
    }

    cd "$PROJECT_ROOT"
    docker compose up -d

    log_info "Docker 服务已启动"
    log_info "前端: http://localhost:7000"
    log_info "后端: http://localhost:7001"
}

# ----------------------------- 停止 -------------------------------------------
stop_all() {
    banner "═══════════════════════════════════════════════════════════════"
    banner "  停止所有 PyTool 服务"
    banner "═══════════════════════════════════════════════════════════════"

    kill_by_pid "$BACKEND_PID_FILE"  "后端"
    kill_by_pid "$FRONTEND_PID_FILE" "前端"

    # 清理残留进程
    pkill -f "uvicorn app:app"  2>/dev/null && log_info "清理残留 uvicorn 进程" || true
    pkill -f "vite"             2>/dev/null && log_info "清理残留 vite 进程"    || true

    log_info "所有服务已停止"
}

# ----------------------------- 状态 -------------------------------------------
show_status() {
    banner "═══════════════════════════════════════════════════════════════"
    banner "  PyTool 服务状态"
    banner "═══════════════════════════════════════════════════════════════"

    # 后端
    if [ -f "$BACKEND_PID_FILE" ] && kill -0 "$(cat "$BACKEND_PID_FILE")" 2>/dev/null; then
        echo -e "  ${GREEN}●${NC} 后端: 运行中 (PID: $(cat "$BACKEND_PID_FILE"), Port: $BACKEND_PORT)"
    elif port_in_use "$BACKEND_PORT"; then
        echo -e "  ${YELLOW}●${NC} 后端: 运行中 (外部进程, Port: $BACKEND_PORT)"
    else
        echo -e "  ${RED}●${NC} 后端: 未运行"
    fi

    # 前端
    if [ -f "$FRONTEND_PID_FILE" ] && kill -0 "$(cat "$FRONTEND_PID_FILE")" 2>/dev/null; then
        echo -e "  ${GREEN}●${NC} 前端: 运行中 (PID: $(cat "$FRONTEND_PID_FILE"), Port: $FRONTEND_PORT)"
    elif port_in_use "$FRONTEND_PORT"; then
        echo -e "  ${YELLOW}●${NC} 前端: 运行中 (外部进程, Port: $FRONTEND_PORT)"
    else
        echo -e "  ${RED}●${NC} 前端: 未运行"
    fi

    # Docker
    if docker compose ps --status running 2>/dev/null | grep -q "pytool"; then
        echo -e "  ${GREEN}●${NC} Docker: 运行中"
    else
        echo -e "  ${GREEN}●${NC} Docker: 未运行"
    fi
}

# ----------------------------- 帮助 -------------------------------------------
show_help() {
    banner "PyTool 启动脚本"
    echo ""
    echo "用法: ./start.sh [命令]"
    echo ""
    echo "命令:"
    echo "  dev        启动后端 + 前端开发服务器 (默认)"
    echo "  backend    仅启动后端"
    echo "  frontend   仅启动前端"
    echo "  docker     使用 Docker Compose 启动"
    echo "  stop       停止所有服务"
    echo "  status     查看服务状态"
    echo "  help       显示此帮助"
    echo ""
    echo "示例:"
    echo "  ./start.sh              # 启动全部开发服务"
    echo "  ./start.sh backend      # 仅启动后端"
    echo "  ./start.sh stop         # 停止所有服务"
    echo "  ./start.sh status       # 查看运行状态"
}

# ----------------------------- 主流程 -----------------------------------------
main() {
    local cmd="${1:-dev}"

    cd "$PROJECT_ROOT"
    setup_dirs

    case "$cmd" in
        dev)
            load_env
            check_deps
            start_backend
            start_frontend
            echo ""
            banner "═══════════════════════════════════════════════════════════════"
            banner "  PyTool 开发服务启动完成！"
            banner "═══════════════════════════════════════════════════════════════"
            echo ""
            echo -e "  前端:  ${GREEN}http://localhost:${FRONTEND_PORT}${NC}"
            echo -e "  后端:  ${GREEN}http://localhost:${BACKEND_PORT}${NC}"
            echo -e "  API:   ${GREEN}http://localhost:${BACKEND_PORT}/api/v1/docs${NC}"
            echo ""
            echo -e "  日志目录: ${LOG_DIR}/"
            echo -e "  停止服务: ./start.sh stop"
            echo -e "  查看状态: ./start.sh status"
            echo ""
            # 实时日志输出（带标签前缀）
            tail -n +1 -f "$BACKEND_LOG" 2>/dev/null | awk -v p="${BLUE}后端:${NC} " '{print p $0; fflush()}' &
            local tail_backend_pid=$!
            tail -n +1 -f "$FRONTEND_LOG" 2>/dev/null | awk -v p="${GREEN}前端:${NC} " '{print p $0; fflush()}' &
            local tail_frontend_pid=$!

            # 前台等待，Ctrl+C 时优雅退出
            trap 'kill $tail_backend_pid $tail_frontend_pid 2>/dev/null; stop_all; exit 0' SIGINT SIGTERM
            log_info "按 Ctrl+C 停止所有服务..."
            while true; do
                sleep 1
                # 检查进程是否存活
                if [ -f "$BACKEND_PID_FILE" ] && ! kill -0 "$(cat "$BACKEND_PID_FILE")" 2>/dev/null; then
                    log_error "后端进程意外退出，查看日志: $BACKEND_LOG"
                    break
                fi
                if [ -f "$FRONTEND_PID_FILE" ] && ! kill -0 "$(cat "$FRONTEND_PID_FILE")" 2>/dev/null; then
                    log_error "前端进程意外退出，查看日志: $FRONTEND_LOG"
                    break
                fi
            done
            kill $tail_backend_pid $tail_frontend_pid 2>/dev/null || true
            ;;
        backend)
            load_env
            check_deps
            start_backend
            log_info "后端运行中，按 Ctrl+C 停止..."
            trap 'kill_by_pid "$BACKEND_PID_FILE" "后端"; exit 0' SIGINT SIGTERM
            wait
            ;;
        frontend)
            load_env
            check_deps
            start_frontend
            log_info "前端运行中，按 Ctrl+C 停止..."
            trap 'kill_by_pid "$FRONTEND_PID_FILE" "前端"; exit 0' SIGINT SIGTERM
            wait
            ;;
        docker)
            start_docker
            ;;
        stop)
            stop_all
            ;;
        status)
            show_status
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $cmd"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
