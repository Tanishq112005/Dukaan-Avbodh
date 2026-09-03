from typing import Optional, List
from sqlmodel import select
from config.database import db_connection
from models import Product, Campaign, CampaignProductLink, CAMPAIGN_WEIGHTS
from models.product import ProductType
from .base_repository import BaseRepository

class ProductRepository(BaseRepository[Product]):
    def __init__(self):
        super().__init__(Product)

    async def update_stock(self, product_id: int, new_stock: int) -> Optional[Product]:
        """Updates stock and, in the same transaction, recomputes importance_score
        (stock * sum of linked campaign weights) so campaign scoring always reflects
        the current stock level. If the product sells out while linked to a live
        campaign, an audit log entry is raised so the merchant sees it."""
        async with db_connection.get_session() as session:
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

    async def get_in_stock(self) -> List[Product]:
        async with db_connection.get_session() as session:
            result = await session.exec(
                select(Product).where(Product.stock > 0)
            )
            return result.all()

    async def get_by_type(self, product_type: ProductType) -> List[Product]:
        """Fetches products of a specific type that are currently in stock."""
        async with db_connection.get_session() as session:
            result = await session.exec(
                # Added Product.stock > 0 to ensure out-of-stock items are filtered out
                select(Product).where(
                    Product.type == product_type, 
                    Product.stock > 0
                )
            )
            return result.all()

    async def get_by_ids(self, product_ids: List[int]) -> List[Product]:
        if not product_ids:
            return []
        async with db_connection.get_session() as session:
            result = await session.exec(select(Product).where(Product.id.in_(product_ids)))
            return result.all()

    async def get_in_stock_by_types(self, product_types: List[ProductType]) -> List[Product]:
        if not product_types:
            return []
        async with db_connection.get_session() as session:
            result = await session.exec(
                select(Product).where(
                    Product.type.in_(product_types),
                    Product.stock > 0,
                )
            )
            return result.all()