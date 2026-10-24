from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .product import Product


class CampaingType(str, Enum):
    HIGH_PRIORITY = "high_priority"
    MEDIUM_PRIORITY = "medium_priority"
    LOW_PRIORITY = "low_priority"


CAMPAIGN_WEIGHTS = {
    CampaingType.LOW_PRIORITY: 1,
    CampaingType.MEDIUM_PRIORITY: 2,
    CampaingType.HIGH_PRIORITY: 3,
}


class CampaignProductLink(SQLModel, table=True):
    campaign_id: Optional[int] = Field(
        default=None, foreign_key="campaign.id", primary_key=True
    )
    product_id: Optional[int] = Field(
        default=None, foreign_key="product.id", primary_key=True
    )


class Campaign(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agenda: str = ""
    discount_percentage: float = 0.0
    priority: int = 0
    type: CampaingType = CampaingType.LOW_PRIORITY
    total_items_sold: int = Field(default=0)
    total_products: int = Field(default=0)
