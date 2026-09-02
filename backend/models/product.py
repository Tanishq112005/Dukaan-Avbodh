from enum import Enum
from typing import List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import event, select

if TYPE_CHECKING:
    from .order import Order

class CampaingType(str, Enum):
    HIGH_PRIORITY = "high_priority"
    MEDIUM_PRIORITY = "medium_priority"
    LOW_PRIORITY = "low_priority"

# Map campaign types to their exact score weights
CAMPAIGN_WEIGHTS = {
    CampaingType.LOW_PRIORITY: 1,
    CampaingType.MEDIUM_PRIORITY: 2,
    CampaingType.HIGH_PRIORITY: 3,
}

class ProductType(str, Enum):
    T_SHIRT = "t-shirt"
    SHORT = "short"
    SHIRT = "shirt"
    HOODIE = "hoodie"
    JEANS = "jeans"

# 1. Join / Link Table
class CampaignProductLink(SQLModel, table=True):
    campaign_id: Optional[int] = Field(
        default=None, foreign_key="campaign.id", primary_key=True
    )
    product_id: Optional[int] = Field(
        default=None, foreign_key="product.id", primary_key=True
    )

# 2. Campaign Model
class Campaign(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agenda: str = ""
    discount_percentage: float = 0.0
    priority: int = 0
    type: CampaingType = CampaingType.LOW_PRIORITY
    
    # Tracks how many items linked to this campaign have been ordered/sold
    total_items_sold: int = Field(default=0) 
    
    # Tracks how many distinct products are currently linked to this campaign
    total_products: int = Field(default=0) 

    products: List["Product"] = Relationship(
        back_populates="campaigns", link_model=CampaignProductLink
    )

# 3. Product Model
class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: float
    cost_price: float = 0.0
    min_profit_margin_percent: float = 20.0
    stock: int
    type: ProductType = ProductType.T_SHIRT
    brand: Optional[str] = None
    gender: Optional[str] = None
    description: Optional[str] = None
    sizes: Optional[str] = None
    rating: float = 4.5
    discount: int = 0
    image_url: Optional[str] = None
    importance_score: int = 0

    orders: List["Order"] = Relationship(back_populates="product")
    campaigns: List[Campaign] = Relationship(
        back_populates="products", link_model=CampaignProductLink
    )

# 4. Trigger: Fetch campaign type and decrease score dynamically
@event.listens_for(CampaignProductLink, "after_delete")
def reduce_product_importance(mapper, connection, target: CampaignProductLink):
    # Get the campaign type to determine how much score to subtract
    campaign_stmt = select(Campaign.type).where(Campaign.id == target.campaign_id)
    campaign_type = connection.scalar(campaign_stmt)

    score_to_subtract = CAMPAIGN_WEIGHTS.get(campaign_type, 1)

    # Deduct the corresponding score from the product
    connection.execute(
        Product.__table__.update()
        .where(Product.__table__.c.id == target.product_id)
        .values(
            importance_score=Product.__table__.c.importance_score - score_to_subtract
        )
    )