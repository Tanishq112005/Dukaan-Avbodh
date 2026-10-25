from typing import Optional, List
from sqlmodel import select
from config.database import db_connection
from Product.models import Product as ProductModel, ProductType


class ProductRepository:
    ### initialization of the class
    def __init__(self, db_connection=None):
        from config.database import db_connection as default_db
        self.db = db_connection or default_db

    ## list of the items in the stock 
    async def get_list_of_items_in_stock(self) -> List[ProductModel]:
        async with self.db.get_session() as session:
            result = await session.exec(
                select(ProductModel).where(ProductModel.stock > 0)
            )
            return result.all()

    ## list of the items in stock by types 
    async def get_list_of_items_in_stock_by_types(self, product_types: List[ProductType]) -> List[ProductModel]:
        if not product_types:
            return []
        async with self.db.get_session() as session:
            result = await session.exec(
                select(ProductModel).where(
                    ProductModel.type.in_(product_types),
                    ProductModel.stock > 0,
                )
            )
            return result.all()

    ## Add the New Product to the database
    async def addProduct(self, product: ProductModel) -> ProductModel: 
        async with self.db.get_session() as session: 
            try: 
                session.add(product)
                await session.commit()
                await session.refresh(product)
                return product
            except Exception as e:
                await session.rollback()
                raise e

    ## get the product by the types
    async def get_by_type(self, product_type: ProductType) -> List[ProductModel]:
        async with self.db.get_session() as session:
            result = await session.exec(
                select(ProductModel).where(ProductModel.type == product_type)
            )
            return result.all()

    ## get the product by the id
    async def get_by_id(self, product_id: int) -> Optional[ProductModel]:
        async with self.db.get_session() as session:
            result = await session.exec(
                select(ProductModel).where(ProductModel.id == product_id)
            )
            return result.first()

    ## get the products by the ids
    async def get_by_ids(self, product_ids: List[int]) -> List[ProductModel]:
        if not product_ids:
            return []
        async with self.db.get_session() as session:
            result = await session.exec(
                select(ProductModel).where(ProductModel.id.in_(product_ids))
            )
            return result.all()

    ## update product
    async def updateProduct(self, product_id: int, update_data: dict) -> Optional[ProductModel]:
        async with self.db.get_session() as session:
            try:
                result = await session.exec(
                    select(ProductModel).where(ProductModel.id == product_id)
                )
                product = result.first()
                if not product:
                    return None
                for key, value in update_data.items():
                    setattr(product, key, value)
                session.add(product)
                await session.commit()
                await session.refresh(product)
                return product
            except Exception as e:
                await session.rollback()
                raise e

    ## Delete the product
    async def deleteProduct(self, product_id: int) -> bool:
        async with self.db.get_session() as session:
            try:
                result = await session.exec(
                    select(ProductModel).where(ProductModel.id == product_id)
                )
                product = result.first()
                if not product:
                    return False
                await session.delete(product)
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                raise e

    ## get all products
    async def get_all_products(self) -> List[ProductModel]:
        try:
            async with self.db.get_session() as session:
                result = await session.exec(
                    select(ProductModel)
                )
                return result.all()

        except Exception:
            raise


Product = ProductRepository
ProductRepository = ProductRepository
productRepository = ProductRepository(db_connection=db_connection)
product_db = productRepository
