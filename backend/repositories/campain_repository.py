from typing import Optional, List
from sqlmodel import select
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

                weight = CAMPAIGN_WEIGHTS.get(type, 1)

                if product_ids:
                    products = (await session.exec(
                        select(Product).where(Product.id.in_(product_ids))
                    )).all()

                    for product in products:
                        product.importance_score += weight
                        session.add(product)
                        session.add(CampaignProductLink(campaign_id=campaign.id, product_id=product.id))

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

                if agenda is not None: campaign.agenda = agenda
                if discount_percentage is not None: campaign.discount_percentage = discount_percentage
                if priority is not None: campaign.priority = priority

                old_weight = CAMPAIGN_WEIGHTS.get(campaign.type, 1)
                if type is not None: campaign.type = type
                new_weight = CAMPAIGN_WEIGHTS.get(campaign.type, 1)

                if product_ids is not None:
                    current_links = (await session.exec(
                        select(CampaignProductLink).where(CampaignProductLink.campaign_id == campaign_id)
                    )).all()
                    current_product_ids = {link.product_id for link in current_links}
                    target_product_ids = set(product_ids)

                    removed_ids = current_product_ids - target_product_ids
                    added_ids = target_product_ids - current_product_ids

                    if removed_ids:
                        campaign.total_products -= len(removed_ids)
                        
                        removed_products = (await session.exec(
                            select(Product).where(Product.id.in_(removed_ids))
                        )).all()
                        for prod in removed_products:
                            prod.importance_score = max(0, prod.importance_score - old_weight)
                            session.add(prod)
                        for link in current_links:
                            if link.product_id in removed_ids:
                                await session.delete(link)

                    if added_ids:
                        campaign.total_products += len(added_ids)
                        
                        added_products = (await session.exec(
                            select(Product).where(Product.id.in_(added_ids))
                        )).all()
                        for prod in added_products:
                            prod.importance_score += new_weight
                            session.add(prod)
                            session.add(CampaignProductLink(campaign_id=campaign_id, product_id=prod.id))
                            
                    campaign.total_products = max(0, campaign.total_products)

                session.add(campaign)
                await session.commit()
                await session.refresh(campaign)
                return campaign
            except Exception as e:
                await session.rollback()
                raise e

    async def delete_campaign(self, campaign_id: int) -> bool:
        """Deletes a campaign and subtracts its importance score weight from all linked products."""
        async with db_connection.get_session() as session:
            try:
                campaign = (await session.exec(select(Campaign).where(Campaign.id == campaign_id))).first()
                if not campaign: return False

                weight = CAMPAIGN_WEIGHTS.get(campaign.type, 1)
                links = (await session.exec(
                    select(CampaignProductLink).where(CampaignProductLink.campaign_id == campaign_id)
                )).all()
                
                product_ids = [link.product_id for link in links]
                if product_ids:
                    products = (await session.exec(select(Product).where(Product.id.in_(product_ids)))).all()
                    for prod in products:
                        prod.importance_score = max(0, prod.importance_score - weight)
                        session.add(prod)

                for link in links:
                    await session.delete(link)
                
                await session.delete(campaign)
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                raise e

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