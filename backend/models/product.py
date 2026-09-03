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

# 4. Trigger: recompute a product's importance_score whenever its campaign links change.
#
# Formula: importance_score = current_stock * sum(priority weight of every campaign
# the product is still linked to). This way the score reflects how much stock is
# actually riding on active campaigns, not just how many campaigns touched it.
# Stock-driven recompute (order placed -> stock drops -> score drops) lives in
# ProductRepository.update_stock, which calls the same helper below.
def recompute_product_importance(connection, product_id: Optional[int]) -> None:
    if product_id is None:
        return

    stock = connection.scalar(select(Product.stock).where(Product.id == product_id))
    if stock is None:
        return

    linked_types = connection.execute(
        select(Campaign.type)
        .select_from(CampaignProductLink)
        .join(Campaign, Campaign.id == CampaignProductLink.campaign_id)
        .where(CampaignProductLink.product_id == product_id)
    ).scalars().all()

    total_weight = sum(CAMPAIGN_WEIGHTS.get(t, 1) for t in linked_types)

    connection.execute(
        Product.__table__.update()
        .where(Product.__table__.c.id == product_id)
        .values(importance_score=stock * total_weight)
    )


@event.listens_for(CampaignProductLink, "after_insert")
def _on_campaign_link_added(mapper, connection, target: CampaignProductLink):
    recompute_product_importance(connection, target.product_id)


@event.listens_for(CampaignProductLink, "after_delete")
def _on_campaign_link_removed(mapper, connection, target: CampaignProductLink):
    recompute_product_importance(connection, target.product_id)