from typing import Optional, List, Dict
from sqlmodel import select, func
from sqlalchemy.orm import selectinload
from config.database import db_connection
from models import Campaign, Product, CampaignProductLink, CAMPAIGN_WEIGHTS, CampaingType
from .base_repository import BaseRepository

class CampaignRepository(BaseRepository[Campaign]):
    def __init__(self):
        super().__init__(Campaign)

    async def get_all_campaigns(self, skip: int = 0, limit: int = 100) -> List[Campaign]:
        """Fetches all campaigns with optional pagination."""
        async with db_connection.get_session() as session:
            result = await session.exec(
                select(Campaign).offset(skip).limit(limit)
            )
            return result.all()

    async def get_campaigns_by_product_ids(self, product_ids: List[int]) -> Dict[int, List[Campaign]]:
        """Maps each product id to the campaigns currently linked to it."""
        mapping: Dict[int, List[Campaign]] = {pid: [] for pid in product_ids}
        if not product_ids:
            return mapping
        async with db_connection.get_session() as session:
            rows = (await session.exec(
                select(CampaignProductLink.product_id, Campaign)
                .join(Campaign, Campaign.id == CampaignProductLink.campaign_id)
                .where(CampaignProductLink.product_id.in_(product_ids))
            )).all()
            seen: Dict[int, set] = {pid: set() for pid in product_ids}
            for product_id, campaign in rows:
                if campaign.id in seen.get(product_id, set()):
                    continue
                seen.setdefault(product_id, set()).add(campaign.id)
                mapping.setdefault(product_id, []).append(campaign)
            return mapping

    async def get_all_campaigns_with_products(self, skip: int = 0, limit: int = 100) -> list[dict]:
        """Campaigns with linked products, serialized before the session closes."""
        async with db_connection.get_session() as session:
            result = await session.execute(
                select(Campaign)
                .options(selectinload(Campaign.products))
                .offset(skip)
                .limit(limit)
            )
            campaigns = result.scalars().unique().all()
            rows = []
            for campaign in campaigns:
                products = []
                for product in campaign.products:
                    products.append({
                        "id": product.id,
                        "name": product.name,
                        "price": product.price,
                        "image_url": product.image_url,
                        "type": product.type.value if hasattr(product.type, "value") else product.type,
                        "importance_score": product.importance_score,
                        "stock": product.stock,
                    })
                rows.append({
                    "id": campaign.id,
                    "agenda": campaign.agenda,
                    "discount_percentage": campaign.discount_percentage,
                    "priority": campaign.priority,
                    "type": campaign.type.value if hasattr(campaign.type, "value") else campaign.type,
                    "total_items_sold": campaign.total_items_sold,
                    # total_products = distinct products linked; total_stock_units = actual
                    # unit count currently sitting in the campaign (sum of each product's stock).
                    # Use total_stock_units when answering "how many items are in this campaign".
                    "total_products": campaign.total_products,
                    "total_stock_units": sum(p["stock"] for p in products),
                    "products": products,
                })
            return rows

    async def create_campaign(
        self, agenda: str, discount_percentage: float, priority: int, 
        type: CampaingType, product_ids: List[int]
    ) -> Campaign:
        """Creates a campaign, sets initial product count, and links products."""
        async with db_connection.get_session() as session:
            try:
                campaign = Campaign(
                    agenda=agenda, 
                    discount_percentage=discount_percentage,
                    priority=priority, 
                    type=type,
                    total_products=len(product_ids) if product_ids else 0
                )
                session.add(campaign)
                await session.flush()

                if product_ids:
                    # importance_score for each linked product is recomputed automatically
                    # (stock * sum of linked campaign weights) by the after_insert trigger
                    # on CampaignProductLink in models/product.py — no manual increment here.
                    session.add_all([
                        CampaignProductLink(campaign_id=campaign.id, product_id=pid)
                        for pid in product_ids
                    ])

                await session.commit()
                await session.refresh(campaign)
                return campaign
            except Exception as e:
                await session.rollback()
                raise e

    async def get_campaign_by_id(self, campaign_id: int) -> Optional[Campaign]:
        """Fetches a single campaign by ID."""
        async with db_connection.get_session() as session:
            result = await session.exec(
                select(Campaign).where(Campaign.id == campaign_id)
            )
            return result.first()

    async def get_campaign_stock_units(self, campaign_id: int) -> int:
        """Sum of current stock across every product still linked to this campaign —
        i.e. how many actual items (not distinct products) are riding on the campaign."""
        async with db_connection.get_session() as session:
            total = await session.scalar(
                select(func.coalesce(func.sum(Product.stock), 0))
                .select_from(CampaignProductLink)
                .join(Product, Product.id == CampaignProductLink.product_id)
                .where(CampaignProductLink.campaign_id == campaign_id)
            )
            return int(total or 0)

    async def update_campaign(
        self, campaign_id: int, agenda: Optional[str] = None, 
        discount_percentage: Optional[float] = None, priority: Optional[int] = None, 
        type: Optional[CampaingType] = None, product_ids: Optional[List[int]] = None
    ) -> Optional[Campaign]:
        """Updates campaign details, synchronizes total_products, and manages scores."""
        async with db_connection.get_session() as session:
            try:
                campaign = (await session.exec(select(Campaign).where(Campaign.id == campaign_id))).first()
                if not campaign: return None

                type_changed = type is not None and type != campaign.type

                if agenda is not None: campaign.agenda = agenda
                if discount_percentage is not None: campaign.discount_percentage = discount_percentage
                if priority is not None: campaign.priority = priority

                if type is not None: campaign.type = type

                current_links = (await session.exec(
                    select(CampaignProductLink).where(CampaignProductLink.campaign_id == campaign_id)
                )).all()
                current_product_ids = {link.product_id for link in current_links}

                if product_ids is not None:
                    target_product_ids = set(product_ids)

                    removed_ids = current_product_ids - target_product_ids
                    added_ids = target_product_ids - current_product_ids

                    # importance_score for affected products is recomputed automatically
                    # (stock * sum of linked campaign weights) by the after_insert/after_delete
                    # triggers on CampaignProductLink in models/product.py.
                    if removed_ids:
                        campaign.total_products -= len(removed_ids)
                        for link in current_links:
                            if link.product_id in removed_ids:
                                await session.delete(link)

                    if added_ids:
                        campaign.total_products += len(added_ids)
                        for pid in added_ids:
                            session.add(CampaignProductLink(campaign_id=campaign_id, product_id=pid))

                    campaign.total_products = max(0, campaign.total_products)

                session.add(campaign)
                await session.flush()

                if type_changed and current_product_ids:
                    # Links didn't change but the weight per link did — the insert/delete
                    # triggers won't fire here, so recompute explicitly.
                    await self.recompute_scores_for_products(session, list(current_product_ids))

                await session.commit()
                await session.refresh(campaign)
                return campaign
            except Exception as e:
                await session.rollback()
                raise e

    async def delete_campaign(self, campaign_id: int) -> bool:
        """Deletes a campaign; linked products' importance_score is recomputed automatically
        (stock * remaining campaign weights) by the after_delete trigger on CampaignProductLink."""
        async with db_connection.get_session() as session:
            try:
                campaign = (await session.exec(select(Campaign).where(Campaign.id == campaign_id))).first()
                if not campaign: return False

                links = (await session.exec(
                    select(CampaignProductLink).where(CampaignProductLink.campaign_id == campaign_id)
                )).all()

                for link in links:
                    await session.delete(link)
                
                await session.delete(campaign)
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                raise e

    async def recompute_scores_for_products(self, session, product_ids: List[int]) -> None:
        """Recomputes importance_score (stock * sum of linked campaign weights) for the given
        products within an existing session/transaction. Use this after a campaign's `type`
        (priority) changes without its product links changing, since the insert/delete
        triggers only fire when a link row is added or removed."""
        if not product_ids:
            return
        products = (await session.exec(select(Product).where(Product.id.in_(product_ids)))).all()
        for product in products:
            types = (await session.exec(
                select(Campaign.type)
                .select_from(CampaignProductLink)
                .join(Campaign, Campaign.id == CampaignProductLink.campaign_id)
                .where(CampaignProductLink.product_id == product.id)
            )).all()
            total_weight = sum(CAMPAIGN_WEIGHTS.get(t, 1) for t in types)
            product.importance_score = product.stock * total_weight
            session.add(product)

    async def record_product_sale(self, product_id: int, quantity_sold: int = 1) -> None:
        """Finds all campaigns linked to a sold product and increments their total_items_sold counter."""
        async with db_connection.get_session() as session:
            try:
                links = (await session.exec(
                    select(CampaignProductLink).where(CampaignProductLink.product_id == product_id)
                )).all()
                
                campaign_ids = [link.campaign_id for link in links]
                
                if not campaign_ids:
                    return

                campaigns = (await session.exec(
                    select(Campaign).where(Campaign.id.in_(campaign_ids))
                )).all()

                for campaign in campaigns:
                    campaign.total_items_sold += quantity_sold
                    session.add(campaign)
                    
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e