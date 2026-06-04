# !/bin/bash

# 后端
cd /workspace/backend
uv run ruff check app
uv run ruff format --check app

# 前端
cd /workspace/frontend
bun lint