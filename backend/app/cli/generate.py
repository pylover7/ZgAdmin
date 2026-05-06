"""代码生成器 — 从模板生成完整 CRUD 模块"""
import re
from pathlib import Path

BACKEND = Path(__file__).parent.parent.parent  # /workspace/backend/


def _pascal(name: str) -> str:
    return "".join(w.capitalize() for w in name.split("_"))


def _field_def(name: str, ftype: str) -> list[str]:
    """将字段定义转为 SQLModel Field 行"""
    label = name  # 用字段名作为中文描述，用户可自行修改
    match ftype:
        case "str":
            return [f"    {name}: str = Field(max_length=255, description=\"{label}\")"]
        case "int":
            return [f"    {name}: int = Field(default=0, description=\"{label}\")"]
        case "float":
            return [f"    {name}: float = Field(default=0.0, description=\"{label}\")"]
        case "bool":
            return [f"    {name}: bool = Field(default=False, description=\"{label}\")"]
        case "uuid":
            return [
                f"    {name}_id: UUID | None = Field(",
                f"        default=None, foreign_key=\"{name}.id\", description=\"{label}\")"
            ]
        case "datetime":
            return [f"    {name}: datetime | None = Field(default=None, nullable=True, description=\"{label}\")"]
        case _:
            return [f"    {name}: {ftype} = Field(description=\"{label}\")"]


def _parse_fields(raw: str) -> list[tuple[str, str]]:
    """解析 'name:str, price:float' → [(name, type), ...]"""
    result = []
    for part in raw.split(","):
        part = part.strip()
        if ":" not in part:
            continue
        name, ftype = part.split(":", 1)
        result.append((name.strip(), ftype.strip()))
    return result


def generate_module(name: str, fields: str, menu_label: str = "") -> list[Path]:
    """生成模块的 model / controller / api，返回创建的文件列表"""
    class_name = _pascal(name)
    field_list = _parse_fields(fields)
    menu_label = menu_label or name

    created = []

    # ── 1. Model ──────────────────────────────────────────────────
    model_path = BACKEND / "app" / "models" / f"{name}.py"
    base_fields = "\n".join(
        line for f in field_list for line in _field_def(*f))
    update_fields = "\n".join(
        f"    {fname}: {ftype} | None = None" for fname, ftype in field_list)

    model_code = f'''from datetime import datetime
from uuid import UUID

from sqlmodel import Field
from .base import BaseModel, TimestampMixin


class {class_name}Base(BaseModel):
{base_fields}


class {class_name}({class_name}Base, TimestampMixin, table=True):
    pass


class {class_name}Create({class_name}Base):
    pass


class {class_name}Update(BaseModel):
{update_fields}


class {class_name}Filter(BaseModel):
    pass
'''
    model_path.write_text(model_code, encoding="utf-8")
    created.append(model_path)

    # ── 2. Controller ─────────────────────────────────────────────
    ctrl_dir = BACKEND / "app" / "controllers"
    ctrl_path = ctrl_dir / f"{name}.py"
    ctrl_code = f'''from app.core.crud import CRUDBase
from app.models import {class_name}, {class_name}Create, {class_name}Update


class {class_name}Controller(CRUDBase[{class_name}, {class_name}Create, {class_name}Update]):
    def __init__(self):
        super().__init__({class_name})


{name}Controller = {class_name}Controller()
'''
    ctrl_path.write_text(ctrl_code, encoding="utf-8")
    created.append(ctrl_path)

    # ── 3. API routes ─────────────────────────────────────────────
    api_dir = BACKEND / "app" / "api" / "v1" / name
    api_dir.mkdir(parents=True, exist_ok=True)

    # __init__.py
    (api_dir / "__init__.py").write_text(f'''from fastapi import APIRouter
from .{name} import router

{name}Router = APIRouter()
{name}Router.include_router(router, tags=["{menu_label}"])
''')

    # route file
    route_code = f'''from uuid import UUID
from fastapi import APIRouter, Query, HTTPException
from sqlmodel import col, and_

from app.controllers.{name} import {name}Controller
from app.core.dependency import SessionDep
from app.models import {class_name}, {class_name}Create, {class_name}Update, {class_name}Filter
from app.models.base import Success, SuccessExtra
from app.settings.log import logger

router = APIRouter()


@router.post("/add", summary="新增{menu_label}")
async def create(session: SessionDep, data: {class_name}Create):
    await {name}Controller.create(session, data)
    await logger.systemInfo("{menu_label}", f"创建: {{data}}")
    return Success(msg="创建成功")


@router.post("/delete", summary="删除{menu_label}")
async def delete(session: SessionDep, data: list[UUID]):
    await {name}Controller.delete(session, data)
    return Success(msg="删除成功")


@router.get("/get", summary="查看{menu_label}")
async def get(session: SessionDep, id: UUID = Query(...)):
    obj = await {name}Controller.get(session, id)
    if not obj:
        raise HTTPException(status_code=404, detail="不存在")
    return Success(data=await obj.to_dict())


@router.post("/list", summary="列表{menu_label}")
async def get_list(
    session: SessionDep,
    data: {class_name}Filter,
    currentPage: int = Query(1),
    pageSize: int = Query(15),
):
    total, items = await {name}Controller.list(
        session, currentPage, pageSize, order=col({class_name}.id).desc())
    result = [await obj.to_dict() for obj in items]
    return SuccessExtra(data=result, total=total, currentPage=currentPage, pageSize=pageSize)


@router.post("/update", summary="更新{menu_label}")
async def update(session: SessionDep, data: {class_name}Update):
    obj = await {name}Controller.get(session, data.id)
    if not obj:
        raise HTTPException(status_code=404, detail="不存在")
    await {name}Controller.update(session, data.id, data)
    await logger.systemInfo("{menu_label}", f"更新: {{data.id}}")
    return Success(msg="更新成功")
'''
    route_path = api_dir / f"{name}.py"
    route_path.write_text(route_code, encoding="utf-8")
    created.append(api_dir / "__init__.py")
    created.append(route_path)

    return created
