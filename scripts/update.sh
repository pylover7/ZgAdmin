#!/usr/bin/env bash
# ==============================================================================
# ZgAdmin — 一键更新脚本
# 职责：拉取最新镜像 + 重启服务
# ==============================================================================
set -eo pipefail

cd "$(dirname "$0")/.."

echo "正在拉取最新镜像..."
docker compose pull zgadmin

echo "正在重启服务..."
docker compose up -d zgadmin

echo "✓ 更新完成！"
