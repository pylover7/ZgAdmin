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

# 暴露后端端口
EXPOSE 7001

# 最终阶段 - 组合前后端
FROM python:3.13-slim

# 安装nginx和其他必要工具和后端依赖
RUN apt-get update && \
  apt-get install -y nginx curl && \
  pip install uv && \
  rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 从前端阶段复制nginx配置和前端文件
COPY --from=frontend /etc/nginx/nginx.conf /etc/nginx/nginx.conf
COPY --from=frontend /usr/share/nginx/html /usr/share/nginx/html

# 从后端阶段复制后端应用
COPY --from=backend /app /backend
# 安装后端依赖
WORKDIR /backend
RUN uv sync --frozen --no-dev

# 创建启动脚本
RUN echo '#!/bin/bash' > /start.sh && \
  echo '# 启动nginx（前端）' >> /start.sh && \
  echo 'nginx -g "daemon off;" &' >> /start.sh && \
  echo '' >> /start.sh && \
  echo '# 等待nginx启动' >> /start.sh && \
  echo 'sleep 3' >> /start.sh && \
  echo '' >> /start.sh && \
  echo '# 启动Python后端' >> /start.sh && \
  echo 'cd /backend' >> /start.sh && \
  echo 'uv run python main.py' >> /start.sh && \
  chmod +x /start.sh

# 暴露端口
EXPOSE 80 7001

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost/api/v1/base/health || exit 1

# 启动命令
CMD ["/start.sh"]
