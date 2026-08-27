# repositories/base_repository.py
from typing import TypeVar, Generic, Type, Optional, List
from sqlmodel import SQLModel, select
from config.database import db_connection

ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def create(self, obj: ModelType) -> ModelType:
        async with db_connection.get_session() as session:
            try:
                session.add(obj)
                await session.commit()
                await session.refresh(obj)
                return obj
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    async def get_by_id(self, obj_id: int) -> Optional[ModelType]:
        async with db_connection.get_session() as session:
            try:
                result = await session.exec(
                    select(self.model).where(self.model.id == obj_id)
                )
                return result.first()
            except Exception as e:
                raise e
            finally:
                await session.close()

    async def get_all(self) -> List[ModelType]:
        async with db_connection.get_session() as session:
            try:
                result = await session.exec(select(self.model))
                return result.all()
            except Exception as e:
                raise e
            finally:
                await session.close()

    async def update(self, obj: ModelType) -> ModelType:
        async with db_connection.get_session() as session:
            try:
                session.add(obj)
                await session.commit()
                await session.refresh(obj)
                return obj
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    async def delete(self, obj_id: int) -> bool:
        async with db_connection.get_session() as session:
            try:
                result = await session.exec(
                    select(self.model).where(self.model.id == obj_id)
                )
                obj = result.first()
                if obj:
                    await session.delete(obj)
                    await session.commit()
                    return True
                return False
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()