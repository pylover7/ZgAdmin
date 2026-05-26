import uuid

from sqlmodel import Field, Relationship, SQLModel

from app.models import User


class ItemBase(SQLModel):
    title: str = Field(
        min_length=1, max_length=255,
        description="标题",
        schema_extra={"examples": ["示例条目"]})
    description: str | None = Field(
        default=None, max_length=255,
        description="描述",
        schema_extra={"examples": ["这是一个示例描述"]})


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(SQLModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="标题",
        schema_extra={"examples": ["更新后的标题"]})
    description: str | None = Field(
        default=None, max_length=255,
        description="描述",
        schema_extra={"examples": ["这是一个示例描述"]})


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, primary_key=True,
        description="主键UUID",
        schema_extra={"examples": ["550e8400-e29b-41d4-a716-446655440000"]})
    title: str = Field(
        max_length=255,
        description="标题",
        schema_extra={"examples": ["示例条目"]})
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE",
        description="所有者用户ID",
        schema_extra={"examples": ["550e8400-e29b-41d4-a716-446655440000"]})
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID = Field(
        description="主键UUID",
        schema_extra={"examples": ["550e8400-e29b-41d4-a716-446655440000"]})
    owner_id: uuid.UUID = Field(
        description="所有者用户ID",
        schema_extra={"examples": ["550e8400-e29b-41d4-a716-446655440000"]})


class ItemsPublic(SQLModel):
    data: list[ItemPublic] = Field(
        description="条目列表")
    count: int = Field(
        description="总数",
        schema_extra={"examples": [0]})
