from typing import Optional, List
from pydantic import BaseModel, Field
from mcp_server_merchant.server import mcp
from models.product import CampaingType, CAMPAIGN_WEIGHTS
from repositories.campain_repository import CampaignRepository

campaign_repo = CampaignRepository()


# --- MCP Resource: Campaign Priority Information ---

@mcp.resource("campaign://priority-weights")
def get_campaign_priority_weights() -> str:
    """Provides information on campaign priority types and their corresponding importance score weights."""
    return """
    Campaign Priority & Importance Score Rules:
    --------------------------------------------
    - HIGH_PRIORITY   ('high_priority')   : Weight = 3 points
    - MEDIUM_PRIORITY ('medium_priority') : Weight = 2 points
    - LOW_PRIORITY    ('low_priority')    : Weight = 1 point

    Behavior:
    - Adding a product to a campaign increases its `importance_score` by the campaign's priority weight.
    - Removing a product (or deleting the campaign) decreases its `importance_score` by the same weight.
    - `total_products` tracks active linked items.
    - `total_items_sold` tracks total volume ordered under the campaign.
    """


# --- Input Schemas ---

class CreateCampaignInput(BaseModel):
    agenda: str = Field(description="The agenda or title of the campaign")
    discount_percentage: float = Field(description="Discount percentage offered in the campaign")
    priority: int = Field(description="Numerical priority of the campaign")
    type: CampaingType = Field(description="Campaign priority type: high_priority, medium_priority, or low_priority")
    product_ids: List[int] = Field(default_factory=list, description="List of product IDs to include in the campaign")


class GetCampaignByIdInput(BaseModel):
    campaign_id: int = Field(description="Unique ID of the campaign to retrieve")


class GetAllCampaignsInput(BaseModel):
    skip: int = Field(default=0, ge=0, description="Number of items to skip for pagination")
    limit: int = Field(default=100, ge=1, le=500, description="Maximum number of items to return")


class UpdateCampaignInput(BaseModel):
    campaign_id: int = Field(description="Unique ID of the campaign to update")
    agenda: Optional[str] = Field(default=None, description="Updated agenda text")
    discount_percentage: Optional[float] = Field(default=None, description="Updated discount percentage")
    priority: Optional[int] = Field(default=None, description="Updated campaign priority level")
    type: Optional[CampaingType] = Field(default=None, description="Updated campaign type")
    product_ids: Optional[List[int]] = Field(default=None, description="Updated list of product IDs linked to the campaign")


class DeleteCampaignInput(BaseModel):
    campaign_id: int = Field(description="Unique ID of the campaign to delete")


class RecordProductSaleInput(BaseModel):
    product_id: int = Field(description="ID of the product that was sold/ordered")
    quantity_sold: int = Field(default=1, ge=1, description="Number of units sold in this order")


# --- MCP Tools ---

@mcp.tool()
async def create_campaign(input_data: CreateCampaignInput) -> dict:
    """Creates a new campaign, links products, sets initial total_products count, and updates product importance scores."""
    campaign = await campaign_repo.create_campaign(
        agenda=input_data.agenda,
        discount_percentage=input_data.discount_percentage,
        priority=input_data.priority,
        type=input_data.type,
        product_ids=input_data.product_ids,
    )
    return {
        "status": "success",
        "message": f"Campaign '{campaign.agenda}' created successfully.",
        "data": campaign.model_dump(),
    }


@mcp.tool()
async def get_campaign_by_id(input_data: GetCampaignByIdInput) -> dict:
    """Retrieves a specific campaign by its ID, including total items sold and how many actual
    units (total_stock_units, i.e. current stock summed across every linked product) are in it.

    LLM Instructions:
    - When the merchant asks "how many items are in this campaign", answer with total_stock_units,
      NOT total_products — total_products only counts distinct products, not units of stock.
    """
    campaign = await campaign_repo.get_campaign_by_id(input_data.campaign_id)
    if not campaign:
        return {"status": "error", "message": f"Campaign with ID {input_data.campaign_id} not found."}

    data = campaign.model_dump()
    data["total_stock_units"] = await campaign_repo.get_campaign_stock_units(input_data.campaign_id)
    return {"status": "success", "data": data}


@mcp.tool()
async def get_all_campaigns(input_data: GetAllCampaignsInput) -> dict:
    """Fetches a list of all campaigns with optional pagination."""
    campaigns = await campaign_repo.get_all_campaigns(skip=input_data.skip, limit=input_data.limit)
    return {
        "status": "success",
        "count": len(campaigns),
        "data": [campaign.model_dump() for campaign in campaigns],
    }


@mcp.tool()
async def update_campaign(input_data: UpdateCampaignInput) -> dict:
    """Updates campaign fields, syncs product links and importance scores, and adjusts total_products count."""
    updated_campaign = await campaign_repo.update_campaign(
        campaign_id=input_data.campaign_id,
        agenda=input_data.agenda,
        discount_percentage=input_data.discount_percentage,
        priority=input_data.priority,
        type=input_data.type,
        product_ids=input_data.product_ids,
    )
    if not updated_campaign:
        return {"status": "error", "message": f"Campaign with ID {input_data.campaign_id} not found."}

    return {
        "status": "success",
        "message": f"Campaign {input_data.campaign_id} updated successfully.",
        "data": updated_campaign.model_dump(),
    }


@mcp.tool()
async def delete_campaign(input_data: DeleteCampaignInput) -> dict:
    """Deletes a campaign and automatically recalculates/subtracts product importance scores."""
    deleted = await campaign_repo.delete_campaign(input_data.campaign_id)
    if not deleted:
        return {"status": "error", "message": f"Campaign with ID {input_data.campaign_id} not found."}

    return {
        "status": "success",
        "message": f"Campaign {input_data.campaign_id} deleted successfully.",
    }


@mcp.tool()
async def record_product_sale(input_data: RecordProductSaleInput) -> dict:
    """Increments the total_items_sold counter for all campaigns associated with a sold product."""
    await campaign_repo.record_product_sale(
        product_id=input_data.product_id,
        quantity_sold=input_data.quantity_sold,
    )
    return {
        "status": "success",
        "message": f"Recorded sale of {input_data.quantity_sold} unit(s) for product ID {input_data.product_id} across linked campaigns.",
    }


@mcp.tool()
async def get_campaign_sales_summary(input_data: GetAllCampaignsInput) -> dict:
    """Provides a breakdown of each campaign's distinct linked products (total_products_linked),
    the actual unit count currently in it (total_stock_units), and sales performance (total_items_sold).

    LLM Instructions:
    - Report total_stock_units, not total_products_linked, when the merchant asks how many
      items/pieces are in a campaign — total_products_linked only counts distinct products.
    """
    campaigns = await campaign_repo.get_all_campaigns(skip=input_data.skip, limit=input_data.limit)

    summary = []
    for c in campaigns:
        summary.append({
            "campaign_id": c.id,
            "agenda": c.agenda,
            "type": c.type,
            "discount_percentage": c.discount_percentage,
            "total_products_linked": c.total_products,
            "total_stock_units": await campaign_repo.get_campaign_stock_units(c.id),
            "total_items_sold": c.total_items_sold,
        })

    return {
        "status": "success",
        "campaign_count": len(summary),
        "data": summary,
    }