#!/usr/bin/env bash
# ==============================================================================
# ZgAdmin — 一键测试脚本
# 用法: ./scripts/test.sh [unit|backend|frontend|e2e|all|coverage]
#   unit      — 运行后端+前端单元测试+覆盖率（默认）
#   backend   — 仅后端测试+覆盖率
#   frontend  — 仅前端测试+覆盖率
#   e2e       — E2E 测试（Playwright）
#   all       — 全部：单元测试 + E2E
#   coverage  — 查看覆盖率报告路径
# ==============================================================================
set -euo pipefail
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
E2E_PASS=""

# ──────────────────────── 后端测试 ──────────────────────────────────────────
run_backend_test() {
    banner "═══════════════════════════════════════════════════════════════"
    banner "  后端单元测试 (pytest + coverage)"
    banner "═══════════════════════════════════════════════════════════════"
    cd "$BACKEND_DIR"

    log_step "安装后端依赖..."
    uv sync --quiet 2>&1 | tail -3

    log_step "运行 pytest + 覆盖率..."
    echo ""
    if uv run pytest --cov --cov-report=term-missing --cov-report=html:htmlcov 2>&1; then
        BACKEND_PASS=true
        log_info "后端测试 ✅ 通过"
    else
        BACKEND_PASS=false
        log_error "后端测试 ❌ 失败"
    fi

    echo ""
}

# ──────────────────────── 前端测试 ──────────────────────────────────────────
run_frontend_test() {
    banner "═══════════════════════════════════════════════════════════════"
    banner "  前端单元测试 (vitest + coverage)"
    banner "═══════════════════════════════════════════════════════════════"
    cd "$FRONTEND_DIR"

    log_step "安装前端依赖..."
    bun install --silent 2>&1 | tail -3

    log_step "运行 vitest + 覆盖率..."
    echo ""
    if bun test:coverage 2>&1; then
        FRONTEND_PASS=true
        log_info "前端测试 ✅ 通过"
    else
        FRONTEND_PASS=false
        log_error "前端测试 ❌ 失败"
    fi

    echo ""
}

# ──────────────────────── E2E 测试 ──────────────────────────────────────────
run_e2e_test() {
    banner "═══════════════════════════════════════════════════════════════"
    banner "  E2E 测试 (Playwright)"
    banner "═══════════════════════════════════════════════════════════════"
    cd "$FRONTEND_DIR"

    log_step "确保 Playwright 浏览器已安装..."
    npx playwright install chromium 2>&1 | tail -3

    log_step "运行 Playwright E2E 测试..."
    echo ""
    if bun test:e2e 2>&1; then
        E2E_PASS=true
        log_info "E2E 测试 ✅ 通过"
    else
        E2E_PASS=false
        log_error "E2E 测试 ❌ 失败"
    fi

    echo ""
}

# ──────────────────────── 覆盖率报告 ────────────────────────────────────────
show_coverage() {
    local backend_report="$BACKEND_DIR/htmlcov/index.html"
    local frontend_report="$FRONTEND_DIR/coverage/lcov-report/index.html"

    echo ""
    banner "覆盖率报告路径:"
    echo ""
    if [ -f "$backend_report" ]; then
        echo -e "  后端: ${GREEN}$backend_report${NC}"
    else
        echo -e "  后端: ${YELLOW}未生成，先运行 ./scripts/test.sh backend${NC}"
    fi
    if [ -f "$frontend_report" ]; then
        echo -e "  前端: ${GREEN}$frontend_report${NC}"
    else
        echo -e "  前端: ${YELLOW}未生成，先运行 ./scripts/test.sh frontend${NC}"
    fi
    echo ""
}

# ──────────────────────── 结果汇总 ──────────────────────────────────────────
print_summary() {
    echo ""
    banner "═══════════════════════════════════════════════════════════════"
    banner "  测试结果汇总"
    banner "═══════════════════════════════════════════════════════════════"
    echo ""

    local all_pass=true

    if [ "$BACKEND_PASS" = true ]; then
        echo -e "  后端单元测试:  ${GREEN}✅ PASS${NC}"
    elif [ "$BACKEND_PASS" = false ]; then
        echo -e "  后端单元测试:  ${RED}❌ FAIL${NC}"
        all_pass=false
    else
        echo -e "  后端单元测试:  ${YELLOW}⏭ SKIP${NC}"
    fi

    if [ "$FRONTEND_PASS" = true ]; then
        echo -e "  前端单元测试:  ${GREEN}✅ PASS${NC}"
    elif [ "$FRONTEND_PASS" = false ]; then
        echo -e "  前端单元测试:  ${RED}❌ FAIL${NC}"
        all_pass=false
    else
        echo -e "  前端单元测试:  ${YELLOW}⏭ SKIP${NC}"
    fi

    if [ "$E2E_PASS" = true ]; then
        echo -e "  E2E 测试:      ${GREEN}✅ PASS${NC}"
    elif [ "$E2E_PASS" = false ]; then
        echo -e "  E2E 测试:      ${RED}❌ FAIL${NC}"
        all_pass=false
    else
        echo -e "  E2E 测试:      ${YELLOW}⏭ SKIP${NC}"
    fi

    echo ""

    if [ "$all_pass" = true ]; then
        banner "  🎉 全部通过！"
        echo ""
        return 0
    else
        banner "  ❌ 存在失败，请检查上方日志"
        echo ""
        return 1
    fi
}

# ──────────────────────── 帮助 ──────────────────────────────────────────────
show_help() {
    echo ""
    banner "ZgAdmin — 一键测试脚本"
    echo ""
    echo "用法: ./scripts/test.sh [命令]"
    echo ""
    echo "命令:"
    echo "  unit      运行后端+前端单元测试+覆盖率（默认）"
    echo "  backend   仅后端测试+覆盖率"
    echo "  frontend  仅前端测试+覆盖率"
    echo "  e2e       E2E 测试（Playwright）"
    echo "  all       全部：单元测试 + E2E"
    echo "  coverage  查看覆盖率报告路径"
    echo ""
    echo "示例:"
    echo "  ./scripts/test.sh              # 运行全部单元测试"
    echo "  ./scripts/test.sh backend      # 仅后端"
    echo "  ./scripts/test.sh all          # 单元 + E2E"
    echo ""
}

# ──────────────────────── 主入口 ────────────────────────────────────────────
main() {
    local cmd="${1:-unit}"
    cd "$PROJECT_ROOT"

    case "$cmd" in
        unit)
            run_backend_test
            run_frontend_test
            print_summary
            ;;
        backend)
            run_backend_test
            print_summary
            ;;
        frontend)
            run_frontend_test
            print_summary
            ;;
        e2e)
            run_e2e_test
            print_summary
            ;;
        all)
            run_backend_test
            run_frontend_test
            run_e2e_test
            print_summary
            ;;
        coverage)
            show_coverage
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
