from typing import Any, Generic, NewType, Type, TypeVar, Optional
from uuid import UUID

from sqlalchemy import ColumnElement, UnaryExpression
from sqlmodel import Session, SQLModel, select, col, func


Total = NewType("Total", int)
ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=SQLModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=SQLModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def create(self, session: Session,
                     obj_in: CreateSchemaType) -> ModelType:
        db_obj = self.model.model_validate(obj_in)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    async def delete(self, session: Session, idList: list[UUID]) -> bool:
        for item in idList:
            db_obj = session.get(self.model, item)
            if db_obj is None:
                continue
            session.delete(db_obj)
        session.commit()
        return True

    async def delete_all(self, session: Session) -> int:
        result = session.exec(select(self.model)).all()
        for item in result:
            session.delete(item)
        session.commit()
        return len(result)

    async def update(self, session: Session, pk: UUID,
                     obj_in: UpdateSchemaType) -> Optional[ModelType]:
        db_obj: Optional[ModelType] = session.get(self.model, pk)
        if db_obj is None:
            return None
        # Update fields manually
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    async def get(self, session: Session, pk: UUID) -> ModelType | None:
        return session.get(self.model, pk)

    async def get_latest(self, session: Session) -> ModelType | None:
        statement = select(self.model).order_by(col(self.model.id).desc())
        return session.exec(statement).first()

    async def all(self, session: Session) -> list[ModelType]:
        return list(session.exec(select(self.model)).all())

    async def list(
            self,
            session: Session,
            currentPage: int = 1,
            pageSize: int = 15,
            where: ColumnElement[bool] | None = None,
            order: UnaryExpression | str = "created_at",
            options: list[Any] | None = None,
    ) -> tuple[Total, list[ModelType]]:
        id_column = getattr(self.model, "id", None)
        if id_column is None:
            raise AttributeError(f"{self.model.__name__} does not have an 'id' attribute")
        count_stmt = select(func.count()).select_from(self.model)
        if where is not None:
            count_stmt = count_stmt.where(where)
        total = session.exec(count_stmt).one()
        statement = select(self.model)
        if options:
            statement = statement.options(*options)
        statement = statement.order_by(order).offset(
            (currentPage - 1) * pageSize).limit(pageSize)
        if where is not None:
            statement = statement.where(where)
        result = session.exec(statement).all()
        return Total(total), list(result)
