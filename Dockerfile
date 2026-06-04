# 多阶段构建 - 前端构建阶段
FROM node:20-alpine AS frontend-builder

# 设置工作目录
WORKDIR /app/frontend

# 复制前端package文件
COPY frontend/package.json frontend/bun.lock ./

# 安装bun
RUN npm install -g bun

# 安装前端依赖
RUN bun install --frozen-lockfile

# 复制项目版本文件（构建时 vite 读取 projectRoot/VERSION）
WORKDIR /app
COPY VERSION .
WORKDIR /app/frontend

# 复制前端源代码
COPY frontend/ ./

# 构建前端应用
RUN bun run build

# 生产阶段 - 前端
FROM nginx:alpine AS frontend

# 从构建阶段复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

# 复制nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

# 暴露前端端口
EXPOSE 80

# 后端阶段
FROM python:3.13-slim AS backend

# 设置工作目录
WORKDIR /app

# 安装uv包管理器
RUN pip install uv

# 复制后端依赖文件
COPY backend/pyproject.toml backend/.python-version backend/uv.lock ./

# 安装后端依赖
RUN uv sync --frozen --no-dev

# 复制后端源代码
COPY backend/ ./

# 最终阶段 - 组合前后端
FROM python:3.13-slim

# 安装nginx和其他必要工具和后端依赖
RUN apt-get update && \
  apt-get install -y nginx && \
  pip install uv && \
  rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 从前端阶段复制nginx配置和前端文件
COPY --from=frontend /etc/nginx/nginx.conf /etc/nginx/nginx.conf
COPY --from=frontend /usr/share/nginx/html /usr/share/nginx/html

# 从后端阶段复制后端应用（.venv 已包含在内，无需再次 uv sync）
COPY --from=backend /app /backend
WORKDIR /backend

# 复制启动脚本
COPY scripts/docker-entrypoint.sh /start.sh
RUN chmod +x /start.sh

# 仅暴露 Nginx 端口（后端通过 Nginx 反代访问，不直接对外）
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost/api/v1/base/health')" || exit 1

# 启动命令
CMD ["/start.sh"]
