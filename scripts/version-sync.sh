#!/bin/bash -e
# scripts/version-sync.sh — 统一版本号到所有子项目

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION=$(cat "$PROJECT_ROOT/VERSION" | tr -d '[:space:]')

echo "🔢 统一版本号: $VERSION"

# 1. 同步 pyproject.toml（用 sed 替换 version 行）
sed -i "s/^version = \".*\"/version = \"$VERSION\"/" \
  "$PROJECT_ROOT/backend/pyproject.toml"

# 2. 同步 platform-config.json
if command -v jq &>/dev/null; then
  jq ".Version = \"$VERSION\"" "$PROJECT_ROOT/frontend/public/platform-config.json" \
    > "$PROJECT_ROOT/frontend/public/platform-config.json.tmp"
  mv "$PROJECT_ROOT/frontend/public/platform-config.json.tmp" \
     "$PROJECT_ROOT/frontend/public/platform-config.json"
else
  sed -i "s/\"Version\": \".*\"/\"Version\": \"$VERSION\"/" \
    "$PROJECT_ROOT/frontend/public/platform-config.json"
fi

echo "✅ 所有文件已同步至 $VERSION"
