#!/usr/bin/env bash
# ==============================================================================
# PyTool — 一键启动脚本
# 用法: ./scripts/start.sh [dev|backend|frontend|sync|stop|status]
# ==============================================================================
set -euo pipefail
export UV_LINK_MODE=copy

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
ENV_FILE="$PROJECT_ROOT/.env"
ENV_EXAMPLE="$PROJECT_ROOT/.env.example"
export VERSION=$(cat "$PROJECT_ROOT/VERSION")

BACKEND_HOST="0.0.0.0"
BACKEND_PORT="7001"
FRONTEND_PORT="7000"
FIRST_RUN=false

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_step()  { echo -e "${BLUE}[STEP]${NC}  $*"; }
banner()    { echo -e "${BOLD}$*${NC}"; }

BACKEND_PID=""
FRONTEND_PID=""

# ──────────────────────── 引导 — 首次运行初始化 ────────────────────────────────
bootstrap() {
    if [ -f "$ENV_FILE" ]; then
        return 0
    fi

    FIRST_RUN=true
    banner "╔══════════════════════════════════════════════════════════════╗"
    banner "║          首次运行 — 正在初始化项目                           ║"
    banner "╚══════════════════════════════════════════════════════════════╝"
    echo ""

    if [ ! -f "$ENV_EXAMPLE" ]; then
        log_error "缺少 .env.example 模板文件"
        exit 1
    fi

    cp "$ENV_EXAMPLE" "$ENV_FILE"
    log_info "已从 .env.example 创建 .env"

    # 检查是否需要设置 SECRET_KEY
    if grep -q "SECRET_KEY=changethis" "$ENV_FILE"; then
        log_warn "SECRET_KEY 仍为默认值 'changethis'"
        log_warn "生产环境请修改: 编辑 .env → 将 SECRET_KEY 替换为随机字符串"
        log_warn "(开发环境无需操作，首次启动会自动生成)"
    fi

    echo ""
    log_info "初始化完成。如需修改配置，编辑根目录 .env 文件"
    echo ""
}

# ──────────────────────── 环境检查 ────────────────────────────────────────────
check_deps() {
    local missing=()

    command -v python3 &>/dev/null || missing+=("python3 (>=3.13)")
    command -v uv       &>/dev/null || missing+=("uv       — pip install uv 或 https://docs.astral.sh/uv/")
    command -v node     &>/dev/null || missing+=("node (>=20)")
    command -v bun      &>/dev/null || missing+=("bun      — curl -fsSL https://bun.sh/install | bash")

    if [ ${#missing[@]} -gt 0 ]; then
        log_error "缺少运行时依赖:"
        for m in "${missing[@]}"; do echo "         $m"; done
        echo ""
        log_info "安装后重新运行: ./scripts/start.sh"
        exit 1
    fi
}

# ──────────────────────── 环境变量加载 ────────────────────────────────────────
load_env() {
    if [ -f "$ENV_FILE" ]; then
        while IFS='=' read -r key value; do
            key=$(echo "$key" | xargs)
            value=$(echo "$value" | xargs | sed 's/^"//;s/"$//')
            case "$key" in
                PORT)      BACKEND_PORT="${value:-$BACKEND_PORT}" ;;
                HOST)      BACKEND_HOST="${value:-$BACKEND_HOST}" ;;
                VITE_PORT) FRONTEND_PORT="${value:-$FRONTEND_PORT}" ;;
            esac
        done < <(grep -v '^\s*#' "$ENV_FILE" | grep '=' || true)
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

# ──────────────────────── 后端 ────────────────────────────────────────────────
run_backend() {
    banner "═══════════════════════════════════════════════════════════════"
    banner "  PyTool 后端 (FastAPI)  http://localhost:${BACKEND_PORT}"
    banner "═══════════════════════════════════════════════════════════════"
    release_port "$BACKEND_PORT"
    log_step "安装后端依赖..."
    cd "$BACKEND_DIR"
    uv sync --no-dev --quiet 2>&1 | tail -3
    log_step "启动后端 (端口 $BACKEND_PORT)..."
    PYTHONUNBUFFERED=1 uv run python main.py &
    BACKEND_PID=$!
}

# ──────────────────────── 前端 ────────────────────────────────────────────────
run_frontend() {
    banner "═══════════════════════════════════════════════════════════════"
    banner "  PyTool 前端 (Vue 3 + Vite)  http://localhost:${FRONTEND_PORT}"
    banner "═══════════════════════════════════════════════════════════════"
    release_port "$FRONTEND_PORT"
    log_step "安装前端依赖..."
    cd "$FRONTEND_DIR"
    bun install --silent 2>&1 | tail -3
    log_step "启动前端 (端口 $FRONTEND_PORT)..."
    bun dev &
    FRONTEND_PID=$!
}

# ──────────────────────── 仅安装依赖 ──────────────────────────────────────────
sync_deps() {
    log_step "安装后端依赖..."
    cd "$BACKEND_DIR"
    uv sync --no-dev
    log_info "后端依赖安装完成"

    log_step "安装前端依赖..."
    cd "$FRONTEND_DIR"
    bun install
    log_info "前端依赖安装完成"

    echo ""
    log_info "依赖全部就绪，运行 ./scripts/start.sh 启动服务"
}

# ──────────────────────── 状态 ────────────────────────────────────────────────
show_status() {
    echo ""
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

# ──────────────────────── 帮助 ────────────────────────────────────────────────
show_help() {
    echo ""
    banner "PyTool — 启动脚本"
    echo ""
    echo "用法: ./scripts/start.sh [命令]"
    echo ""
    echo "命令:"
    echo "  dev        启动前后端开发服务器（默认）"
    echo "  backend    仅启动后端"
    echo "  frontend   仅启动前端"
    echo "  sync       仅安装依赖，不启动服务"
    echo "  stop       停止所有服务"
    echo "  status     查看运行状态"
    echo ""
    echo "首次运行: 脚本会自动从 .env.example 创建 .env 配置文件"
    echo ""
    echo "示例:"
    echo "  ./scripts/start.sh            # 一键启动"
    echo "  ./scripts/start.sh sync       # 仅安装依赖"
    echo "  ./scripts/start.sh status     # 查看状态"
    echo "  ./scripts/start.sh stop       # 停止服务"
    echo ""
}

# ──────────────────────── 主入口 ──────────────────────────────────────────────
main() {
    local cmd="${1:-dev}"
    cd "$PROJECT_ROOT"

    case "$cmd" in
        dev)
            bootstrap; check_deps; load_env
            run_backend; run_frontend
            echo ""
            banner "═══════════════════════════════════════════════════════════════"
            banner "  PyTool 已启动"
            banner "═══════════════════════════════════════════════════════════════"
            echo ""
            echo -e "  前端: ${GREEN}http://localhost:${FRONTEND_PORT}${NC}"
            echo -e "  后端: ${GREEN}http://localhost:${BACKEND_PORT}${NC}"
            echo -e "  API:  ${GREEN}http://localhost:${BACKEND_PORT}/api/v1/docs${NC}"
            echo ""
            echo -e "  默认管理员: admin / admin123456"
            echo -e "  按 ${YELLOW}Ctrl+C${NC} 停止"
            echo ""
            $FIRST_RUN && log_info "首次运行？编辑 .env 配置数据库等选项后重新启动"
            wait -n 2>/dev/null || wait
            log_error "某个服务已退出"
            ;;
        backend)
            bootstrap; check_deps; load_env
            run_backend
            log_info "后端运行中，Ctrl+C 停止..."
            wait "$BACKEND_PID"
            ;;
        frontend)
            bootstrap; check_deps; load_env
            run_frontend
            log_info "前端运行中，Ctrl+C 停止..."
            wait "$FRONTEND_PID"
            ;;
        sync)
            check_deps
            sync_deps
            trap - EXIT
            ;;
        stop)
            release_port "$BACKEND_PORT"
            release_port "$FRONTEND_PORT"
            log_info "已停止"
            trap - EXIT
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
