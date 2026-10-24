from typing import Optional, List
from sqlmodel import select
from config.database import db_connection
from models import Product, Campaign, CampaignProductLink, CAMPAIGN_WEIGHTS
from models.product import ProductType
from .base_repository import BaseRepository

class Product(BaseRepository[Product]):
    
    ### initilization of the class
    def __init__(self , db_connection):
        super().__init__(Product)
        self.db = db_connection

    async def update_stock(self, product_id: int, new_stock: int) -> Optional[Product]:
        """Updates stock and, in the same transaction, recomputes importance_score
        (stock * sum of linked campaign weights) so campaign scoring always reflects
        the current stock level. If the product sells out while linked to a live
        campaign, an audit log entry is raised so the merchant sees it."""
        async with self.db.get_session() as session:
            try:
                result = await session.exec(
                    select(Product).where(Product.id == product_id)
                )
                product = result.first()
                if not product:
                    return None

                new_stock = max(0, new_stock)
                product.stock = new_stock

                linked = (await session.exec(
                    select(Campaign)
                    .select_from(CampaignProductLink)
                    .join(Campaign, Campaign.id == CampaignProductLink.campaign_id)
                    .where(CampaignProductLink.product_id == product_id)
                )).all()

                total_weight = sum(CAMPAIGN_WEIGHTS.get(c.type, 1) for c in linked)
                product.importance_score = new_stock * total_weight

                session.add(product)
                await session.commit()
                await session.refresh(product)

                if new_stock == 0 and linked:
                    try:
                        from services.audit_logger import audit_logger
                        await audit_logger.log_action(
                            action="product_sold_out_in_campaign",
                            reason=f"'{product.name}' (id={product.id}) just hit 0 stock while linked to "
                                   f"{len(linked)} active campaign(s).",
                            result=f"campaigns={[c.agenda or c.id for c in linked]}",
                            user_id=None,
                            thread_id=None,
                            metadata={
                                "kind": "stock_alert",
                                "product_id": product.id,
                                "product_name": product.name,
                                "campaign_ids": [c.id for c in linked],
                            },
                        )
                    except Exception as log_err:
                        print(f"[STOCK] Could not write sold-out audit log: {log_err}")

                return product
            except Exception as e:
                await session.rollback()
                raise e

    async def decrement_stocks_batch(self, quantities: dict[int, int]) -> List[Product]:
        """Decrements stock and recomputes importance_score for multiple products in a single session,
        preventing N+1 stock update round-trips during checkout."""
        if not quantities:
            return []
        async with self.db.get_session() as session:
            try:
                product_ids = list(quantities.keys())
                products = (await session.exec(
                    select(Product).where(Product.id.in_(product_ids))
                )).all()

                # Batch fetch all linked campaigns for these products
                rows = (await session.exec(
                    select(CampaignProductLink.product_id, Campaign)
                    .join(Campaign, Campaign.id == CampaignProductLink.campaign_id)
                    .where(CampaignProductLink.product_id.in_(product_ids))
                )).all()

                campaigns_by_product: dict[int, list[Campaign]] = {pid: [] for pid in product_ids}
                for pid, c in rows:
                    campaigns_by_product.setdefault(pid, []).append(c)

                sold_out_products = []
                for product in products:
                    deduct = quantities.get(product.id, 1)
                    new_stock = max(0, product.stock - deduct)
                    product.stock = new_stock

                    linked = campaigns_by_product.get(product.id, [])
                    total_weight = sum(CAMPAIGN_WEIGHTS.get(c.type, 1) for c in linked)
                    product.importance_score = new_stock * total_weight
                    session.add(product)

                    if new_stock == 0 and linked:
                        sold_out_products.append((product, linked))

                await session.commit()
                for p in products:
                    await session.refresh(p)

                if sold_out_products:
                    try:
                        from services.audit_logger import audit_logger
                        for product, linked in sold_out_products:
                            await audit_logger.log_action(
                                action="product_sold_out_in_campaign",
                                reason=f"'{product.name}' (id={product.id}) just hit 0 stock while linked to "
                                       f"{len(linked)} active campaign(s).",
                                result=f"campaigns={[c.agenda or c.id for c in linked]}",
                                user_id=None,
                                thread_id=None,
                                metadata={
                                    "kind": "stock_alert",
                                    "product_id": product.id,
                                    "product_name": product.name,
                                    "campaign_ids": [c.id for c in linked],
                                },
                            )
                    except Exception as log_err:
                        print(f"[STOCK] Could not write sold-out audit log: {log_err}")

                return products
            except Exception as e:
                await session.rollback()
                raise e

    async def get_in_stock(self) -> List[Product]:
        async with self.db.get_session() as session:
            result = await session.exec(
                select(Product).where(Product.stock > 0)
            )
            return result.all()

    
    

    async def get_in_stock_by_types(self, product_types: List[ProductType]) -> List[Product]:
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
        
    
         
            