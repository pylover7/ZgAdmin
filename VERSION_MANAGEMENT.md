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

### VS Code 集成

项目已配置了便捷的 VS Code 终端脚本，可以一键管理版本：

#### 终端配置

在 VS Code 中，按 `Ctrl+Shift+P` 打开命令面板，输入 "Terminal: Select Default Profile"，然后选择以下任意一个配置：

#### 可用的终端脚本

1. **更新版本-补丁** - 递增补丁版本号 (1.0.0 → 1.0.1)
2. **更新版本-次版本** - 递增次版本号 (1.0.0 → 1.1.0)
3. **更新版本-主版本** - 递增主版本号 (1.0.0 → 2.0.0)
4. **更新版本-自定义** - 输入自定义版本号进行更新
5. **同步版本信息** - 同步所有文件的版本信息
6. **查看当前版本** - 显示当前项目的版本信息

#### 使用方法

1. 在 VS Code 中按 `Ctrl+Shift+` \` (反引号键) 打开终端
2. 点击终端右上角的 `+` 号旁边的下拉箭头
3. 选择对应的版本管理脚本
4. 根据提示操作即可

### 自动化集成

可以将版本管理集成到 CI/CD 流程中：

```bash
# 在 CI/CD 中自动更新版本
NEW_VERSION=$(date +%Y.%m.%d)
echo $NEW_VERSION > VERSION
python scripts/update-version.py --no-build
```

这样可以确保每次部署都有明确的版本标识，便于问题追踪和回滚。