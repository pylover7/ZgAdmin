# 版本管理说明

## 项目版本控制方案

本项目采用统一的版本管理策略，通过 `VERSION` 文件控制整个项目的版本号。

### 版本文件位置

```
/workspace/VERSION
```

### 版本管理方式

#### 1. 手动更新版本

编辑 `VERSION` 文件，修改版本号：
```
1.0.0
```

#### 2. 使用脚本更新版本

```bash
# 更新所有文件的版本号为 1.2.3
python scripts/update-version.py 1.2.3

# 只更新前端版本
python scripts/update-version.py 1.2.3 --frontend-only

# 只更新后端版本
python scripts/update-version.py 1.2.3 --backend-only

# 使用 VERSION 文件中的版本号更新所有文件
python scripts/update-version.py
```

### 版本同步位置

脚本会自动更新以下文件的版本信息：

1. **前端版本**
   - `frontend/package.json` - npm 包版本
   - `frontend/.env.version` - 前端环境变量版本

2. **后端版本**
   - `backend/pyproject.toml` - Python 包版本
   - `backend/app/settings/__init__.py` - 后端设置版本（动态读取）

3. **文档版本**
   - `README.md` - 项目说明文档版本
   - `Dockerfile` - Docker 构建版本标签

4. **统一版本源**
   - `VERSION` - 项目根目录版本文件

### 版本获取方式

#### 后端获取版本

```python
from app.settings import get_settings

settings = get_settings()
version = settings.VERSION
```

#### API 接口获取版本

```bash
# 获取版本信息
GET /api/v1/system/version/info

# 健康检查（包含版本信息）
GET /api/v1/system/version/health
```

#### 前端获取版本

前端可以通过以下方式获取版本：

1. 从环境变量读取（推荐）：
```typescript
const version = import.meta.env.VITE_APP_VERSION
```

2. 从 API 接口获取：
```typescript
const response = await fetch('/api/v1/system/version/info')
const { version } = await response.json()
```

### 版本命名规范

建议使用语义化版本（Semantic Versioning）：

- `MAJOR.MINOR.PATCH`
- `1.0.0` - 主版本.次版本.修订版本
- 主版本：不兼容的 API 修改
- 次版本：向下兼容的功能性新增
- 修订版本：向下兼容的问题修正

### 构建时的版本信息

- Docker 容器会包含版本环境变量 `VERSION`
- 构建产物会自动包含当前版本信息
- 日志和错误信息会显示当前版本

### 注意事项

1. 修改 `VERSION` 文件后，建议运行更新脚本同步所有相关文件
2. 前端构建时会自动使用 `package.json` 中的版本号
3. 后端启动时会动态读取 `VERSION` 文件
4. 版本信息会显示在系统的各个角落，包括 API 响应、日志、错误页面等

### 自动化集成

可以将版本管理集成到 CI/CD 流程中：

```bash
# 在 CI/CD 中自动更新版本
NEW_VERSION=$(date +%Y.%m.%d)
echo $NEW_VERSION > VERSION
python scripts/update-version.py
```

这样可以确保每次部署都有明确的版本标识，便于问题追踪和回滚。