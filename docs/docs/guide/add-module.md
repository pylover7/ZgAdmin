# 添加新模块

手动创建完整 CRUD 模块的步骤。

## 1. 创建数据模型

在 `backend/app/models/` 下新建模型文件，例如 `product.py`：

```python
from sqlmodel import SQLModel, Field
from datetime import datetime
import uuid

class ProductBase(SQLModel):
    name: str = Field(max_length=255, index=True)
    price: float = Field(default=0.0)
    category: str = Field(max_length=100, default="")

class Product(ProductBase, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ProductCreate(ProductBase):
    """创建时的输入模型"""

class ProductUpdate(SQLModel):
    """更新时的输入模型（所有字段可选）"""
    name: str | None = None
    price: float | None = None
    category: str | None = None
```

> **约定**：模型名用 `*Base` / `*Create` / `*Update` 变体，主键用 UUID4 字符串。

## 2. 注册模型

编辑 `backend/app/models/__init__.py`，添加一行：

```python
from .product import *
```

## 3. 创建控制器

在 `backend/app/controllers/` 下新建 `product.py`：

```python
from app.controllers.base import CRUDBase
from app.models.product import Product, ProductCreate, ProductUpdate

class ProductController(CRUDBase[Product, ProductCreate, ProductUpdate]):
    """商品控制器"""

product_controller = ProductController(Product)
```

> `CRUDBase` 已提供 `get`/`get_multi`/`create`/`update`/`remove` 等通用方法。

## 4. 创建路由

在 `backend/app/api/v1/` 下创建目录和路由文件，例如 `product/__init__.py`：

```python
from fastapi import APIRouter, Depends
from app.api.deps import DependPermission
from app.controllers.product import product_controller
from app.models.product import ProductCreate, ProductUpdate

productRouter = APIRouter()

@productRouter.post("/list", dependencies=[DependPermission])
async def list_products(page: int = 1, pageSize: int = 10):
    return await product_controller.get_multi(page=page, pageSize=pageSize)

@productRouter.post("/add", dependencies=[DependPermission])
async def add_product(obj: ProductCreate):
    return await product_controller.create(obj_in=obj)

@productRouter.post("/update", dependencies=[DependPermission])
async def update_product(obj: ProductUpdate):
    return await product_controller.update(obj_in=obj)

@productRouter.post("/delete", dependencies=[DependPermission])
async def delete_product(ids: list[str]):
    return await product_controller.remove(ids=ids)
```

## 5. 注册路由

编辑 `backend/app/api/v1/__init__.py`，添加：

```python
from .product import productRouter
# ...
v1_router.include_router(productRouter, prefix="/product", dependencies=[DependPermission])
```

## 6. 添加菜单

编辑 `backend/app/seed/data/menus.py`，在合适的父菜单下添加：

```python
dict(menuType=0, title="menus.product", name="Product",
     path="/product", component="product/index", icon="ri:shopping-bag-line", rank=1),
```

同时在 `locales/zh-CN.yaml` 和 `locales/en.yaml` 添加翻译：

```yaml
# zh-CN.yaml
menus:
  product: 商品管理

# en.yaml
menus:
  product: Products
```

## 7. 创建前端页面

在 `frontend/src/views/` 下创建页面目录和组件：

```
frontend/src/views/product/
├── index.vue        # 列表页
├── form.vue         # 表单弹窗（可选）
└── utils/
    ├── hooks.tsx    # 页面逻辑
    └── types.ts     # 类型定义
```

在 `frontend/src/api/` 下创建 API 封装，例如 `product.ts`。

## 8. 数据库迁移

```bash
cd backend
uv run alembic revision --autogenerate -m "add product table"
uv run alembic upgrade head
```

## 9. 重启服务

```bash
./scripts/start.sh
```

启动后：
- 数据库自动创建 `product` 表
- 菜单自动同步到前端
- API 路由自动注册到权限表

## 常用字段类型

| Python 类型 | SQLModel Field | SQL 类型 |
|------------|---------------|---------|
| `str` | `Field(max_length=255)` | VARCHAR(255) |
| `int` | `Field(default=0)` | INTEGER |
| `float` | `Field(default=0.0)` | FLOAT |
| `bool` | `Field(default=False)` | BOOLEAN |
| `datetime` | `Field(default_factory=datetime.now)` | DATETIME |
| `str` (UUID) | `Field(foreign_key="table.id")` | VARCHAR (外键) |
