from typing import Optional, List
from sqlmodel import select
from config.database import db_connection
from models import Product
from models.product import ProductType


class Product:
    
    ### initilization of the class
    def __init__(self , db_connection):
        self.db = db_connection
    
    ## list of the items in the stock 
    async def get_list_of_items_in_stock(self) -> List[Product]:
        async with self.db.get_session() as session:
            result = await session.exec(
                select(Product).where(Product.stock > 0)
            )
            return result.all()

    
    ## list of the items in stock by types 
    async def get_list_of_items_in_stock_by_types(self, product_types: List[ProductType]) -> List[Product]:
        if not product_types:
            return []
        async with self.db.get_session() as session:
            result = await session.exec(
                select(Product).where(
                    Product.type.in_(product_types),
                    Product.stock > 0,
                )
            )
            return result.all()
    
    
    ## Add the New Product to the database
    async def addProduct(self , product: Product) -> Product: 
        
        async with self.db.get_session() as session: 
            try: 
                session.add(product)
                await session.commit()
                await session.refresh(product)
                return product
            except Exception as e:
                await session.rollback()
                raise e
    
    
    ## Make the Changes in the Product in the database
    ## await repository.updateProduct(10, {"stock": 20}) example to use this function
    async def updateProduct(
       self, product_id: int, updates: dict
       ) -> Optional[Product]:

       async with self.db.get_session() as session:
        try:
            product = await session.get(Product, product_id)

            if not product:
                return None

            for key, value in updates.items():
                if hasattr(product, key):
                    setattr(product, key, value)

            await session.commit()
            await session.refresh(product)

            return product

        except Exception:
            await session.rollback()
            raise
        
    ## Delete the Product from the database 
    async def deleteProduct(self , product_id: int ) -> bool:
        async with self.db.get_session() as session:
            try:
                product = await session.get(Product, product_id)
                if not product:
                    return False
                await session.delete(product)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise    
    
    
    ## Get the product by its type and also check if the product is in stock or not      
    async def get_by_type(self, product_type: ProductType) -> List[Product]:
        """Fetches products of a specific type that are currently in stock."""
        async with self.db.get_session() as session:
            result = await session.exec(
                # Added Product.stock > 0 to ensure out-of-stock items are filtered out
                select(Product).where(
                    Product.type == product_type, 
                    Product.stock > 0
                )
            )
            return result.all()
        
    
    ## Get the products by their ids 
    async def get_by_ids(self, product_ids: List[int]) -> List[Product]:
       
        if not product_ids:
            print("Empty List of product_ids provided to get_by_ids. Returning empty list")
            return []
        
        async with self.db.get_session() as session:
            result = await session.exec(select(Product).where(Product.id.in_(product_ids)))
            return result.all()    
        
        
    ## Get the all the products 
    async def get_all_products(self) -> List[Product]:
      try:
         async with self.db.get_session() as session:
            result = await session.exec(
                select(Product)
            )
            return result.all()

      except Exception:
         raise


productRepository = Product(db_connection=db_connection)
    
         
            