# 添加新模块

用 CLI 代码生成器一行命令生成完整 CRUD。

## 1. 生成模块

```bash
cd backend
uv run python -m app.cli generate-module product \
  --fields "name:str, price:float, category:str" \
  --menu "商品管理"
```

生成 4 个文件：
- `app/models/product.py` — 数据模型
- `app/controllers/product.py` — CRUD 控制器
- `app/api/v1/product/__init__.py` — 路由注册
- `app/api/v1/product/product.py` — 5 个 REST 端点

## 2. 注册模型

编辑 `backend/app/models/__init__.py`，添加一行：

```python
from .product import *
```

## 3. 注册路由

编辑 `backend/app/api/v1/__init__.py`，添加：

```python
from .product import productRouter
# ...
v1_router.include_router(productRouter, prefix="/product", dependencies=[DependPermission])
```

## 4. 添加菜单

编辑 `backend/app/seed/data/menus.py`，在合适的父菜单下添加：

```python
dict(menuType=0, title="商品管理", name="Product",
     path="/product", component="product/index", icon="ri:shopping-bag-line", rank=1),
```

## 5. 重启服务

```bash
./scripts/start.sh
```

数据库和菜单会自动重建。

## 支持的字段类型

| 简写 | 生成的 Field |
|---|---|
| `str` | `Field(max_length=255)` |
| `int` | `Field(default=0)` |
| `float` | `Field(default=0.0)` |
| `bool` | `Field(default=False)` |
| `uuid` | `Field(foreign_key=...)` |
| `datetime` | `Field(nullable=True)` |

## 更多示例

```bash
# 简单模块
uv run python -m app.cli generate-module tag \
  --fields "name:str" --menu "标签管理"

# 含关联字段
uv run python -m app.cli generate-module order \
  --fields "user_id:uuid, amount:float, status:str, paid_at:datetime" \
  --menu "订单管理"
```
