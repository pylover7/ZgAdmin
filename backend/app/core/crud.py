from typing import Generic, NewType, Type, TypeVar, Optional, Union
from uuid import UUID

from click import Option
from sqlmodel import Session, SQLModel, Column, select, col, func


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

    async def delete(self, session: Session, idList: list[str]) -> bool:
        for item in idList:
            db_obj = session.get(self.model, UUID(item))
            if db_obj is None:
                continue
            session.delete(db_obj)
        session.commit()
        return True

    async def update(self, session: Session, id: str,
                     obj_in: UpdateSchemaType) -> Optional[ModelType]:
        db_obj: Optional[ModelType] = session.get(self.model, UUID(id))
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

    async def get(self, session: Session, id: str) -> ModelType | None:
        return session.get(self.model, UUID(id))

    async def get_latest(self, session: Session) -> ModelType | None:
        statement = select(self.model).order_by(col("id").desc())
        return session.exec(statement).first()

    async def all(self, session: Session) -> list[ModelType]:
        return list(session.exec(select(self.model)).all())

    async def list(
            self,
            session: Session,
            currentPage: int = 1,
            pageSize: int = 15,
            where: Column | None = None,
            order: Column | str = "created_at"
    ) -> tuple[Total, list[ModelType]]:
        id_column = getattr(self.model, "id", None)
        if id_column is None:
            raise AttributeError(f"{self.model.__name__} does not have an 'id' attribute")
        total = session.exec(select(func.count(id_column))).one()
        statement = select(
            self.model).order_by(order).offset(
            (currentPage - 1) * pageSize).limit(pageSize)
        if where is not None:
            statement = statement.where(where)
        result = session.exec(statement).all()
        return Total(total), list(result)
