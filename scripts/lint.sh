#!/usr/bin/env bash
# ==============================================================================
# ZgAdmin — 一键 Lint 脚本
# ==============================================================================
set -Eeuo pipefail
export UV_LINK_MODE=copy

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_step()  { echo -e "${BLUE}[STEP]${NC}  $*"; }
banner()    { echo -e "${BOLD}$*${NC}"; }

BACKEND_PASS=""
FRONTEND_PASS=""

# ──────────────────────── 后端 Lint ──────────────────────────────────────────
run_backend_lint() {
    banner "═══════════════════════════════════════════════════════════════"
    banner "  后端 Lint (Ruff)"
    banner "═══════════════════════════════════════════════════════════════"
    cd "$BACKEND_DIR"

    log_step "自动修复可修复的问题..."
    uv run ruff check --fix app/ 2>&1 || true
    uv run ruff format app/ 2>&1 || true
    echo ""

    log_step "检查剩余问题..."
    local check_failed=false

    if ! uv run ruff check app/ 2>&1; then
        check_failed=true
    fi

    if ! uv run ruff format --check app/ 2>&1; then
        check_failed=true
    fi

    if [[ "$check_failed" == "false" ]]; then
        BACKEND_PASS=true
        log_info "后端 Lint ✅ 通过"
    else
        BACKEND_PASS=false
        log_error "后端 Lint ❌ 存在问题"
    fi

    echo ""
}

# ──────────────────────── 前端 Lint ──────────────────────────────────────────
run_frontend_lint() {
    banner "═══════════════════════════════════════════════════════════════"
    banner "  前端 Lint (ESLint + Prettier + Stylelint)"
    banner "═══════════════════════════════════════════════════════════════"
    cd "$FRONTEND_DIR"

    if [[ ! -x "node_modules/.bin/eslint" ]]; then
        log_step "安装前端依赖..."
        bun install 2>&1 | tail -5
    fi

    log_step "运行 bun lint（自动修复 + 检查）..."
    echo ""
    if bun lint 2>&1; then
        FRONTEND_PASS=true
        log_info "前端 Lint ✅ 通过"
    else
        FRONTEND_PASS=false
        log_error "前端 Lint ❌ 存在问题"
    fi

    echo ""
}

# ──────────────────────── 结果汇总 ──────────────────────────────────────────
print_summary() {
    echo ""
    banner "═══════════════════════════════════════════════════════════════"
    banner "  Lint 结果汇总"
    banner "═══════════════════════════════════════════════════════════════"
    echo ""

    local all_pass=true

    if [[ "$BACKEND_PASS" == "true" ]]; then
        echo -e "  后端 Lint:  ${GREEN}✅ PASS${NC}"
    elif [[ "$BACKEND_PASS" == "false" ]]; then
        echo -e "  后端 Lint:  ${RED}❌ FAIL${NC}"
        all_pass=false
    else
        echo -e "  后端 Lint:  ${YELLOW}⏭ SKIP${NC}"
    fi

    if [[ "$FRONTEND_PASS" == "true" ]]; then
        echo -e "  前端 Lint:  ${GREEN}✅ PASS${NC}"
    elif [[ "$FRONTEND_PASS" == "false" ]]; then
        echo -e "  前端 Lint:  ${RED}❌ FAIL${NC}"
        all_pass=false
    else
        echo -e "  前端 Lint:  ${YELLOW}⏭ SKIP${NC}"
    fi

    echo ""

    if [[ "$all_pass" == "true" ]]; then
        banner "  🎉 全部通过！"
        echo ""
        return 0
    else
        banner "  ❌ 存在问题，请检查上方日志"
        echo ""
        return 1
    fi
}

# ──────────────────────── 主入口 ────────────────────────────────────────────
cd "$PROJECT_ROOT"
run_backend_lint
run_frontend_lint
print_summary
