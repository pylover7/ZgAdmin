#!/usr/bin/env bash
# ==============================================================================
# ZgAdmin — 文档构建并部署到 EdgeOne Pages
# 用法: ./scripts/deploy-docs.sh
# ==============================================================================
set -euo pipefail

# 颜色输出
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

# 配置
BUILD_DIR="docs/.vitepress/dist"
PROJECT_NAME="zgadmin"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DOCS_DIR="$PROJECT_ROOT/docs"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN} ZgAdmin 文档构建部署脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# ── [1/4] 检查环境 ──────────────────────────────────────────────────────────
echo -e "\n${YELLOW}[1/4] 检查环境...${NC}"

if ! command -v bun &>/dev/null; then
    echo -e "${RED}错误: bun 未安装${NC}"
    echo "请先安装 bun: curl -fsSL https://bun.sh/install | bash"
    exit 1
fi

if [ -z "${EDGEONE_API_TOKEN:-}" ]; then
    echo -e "${RED}错误: EDGEONE_API_TOKEN 环境变量未设置${NC}"
    echo "请先设置: export EDGEONE_API_TOKEN=your_token"
    exit 1
fi

# ── [2/4] 安装依赖 ──────────────────────────────────────────────────────────
echo -e "\n${YELLOW}[2/4] 安装依赖...${NC}"
cd "$DOCS_DIR"
bun install

# ── [3/4] 构建 VitePress ────────────────────────────────────────────────────
echo -e "\n${YELLOW}[3/4] 清理并构建 VitePress...${NC}"
rm -rf "$BUILD_DIR"
bun run docs:build

if [ ! -d "$BUILD_DIR" ]; then
    echo -e "${RED}错误: 构建失败，目录 $BUILD_DIR 不存在${NC}"
    exit 1
fi

BUILD_SIZE=$(du -sh "$BUILD_DIR" | cut -f1)
echo -e "${GREEN}构建完成! 大小: $BUILD_SIZE${NC}"

# ── [4/4] 部署到 EdgeOne ────────────────────────────────────────────────────
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN} 部署到 EdgeOne${NC}"
echo -e "${GREEN}========================================${NC}"

cd "$DOCS_DIR"
bun run edgeone pages deploy "$DOCS_DIR/$BUILD_DIR" -n "$PROJECT_NAME" -t "$EDGEONE_API_TOKEN"

echo -e "\n${GREEN}✅ 部署完成!${NC}"
echo -e "${GREEN}访问地址: https://zgadmin.pylover.net${NC}"
