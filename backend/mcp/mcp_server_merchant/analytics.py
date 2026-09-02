from typing import Optional
from pydantic import BaseModel, Field
from mcp_server_merchant.server import mcp
from repositories.analytics_repository import AnalyticsRepository

analytics_repo = AnalyticsRepository()


# --- Input Schemas ---

class GetProductSalesDetailsInput(BaseModel):
    product_id: int = Field(description="Unique ID of the product to fetch sales analytics for")
    status: str = Field(
        default="completed", 
        description="Filter orders by status (e.g., 'completed', 'pending', 'cancelled')"
    )


class GetSalesByCategoryInput(BaseModel):
    status: str = Field(
        default="completed", 
        description="Filter orders by status (e.g., 'completed', 'pending', 'cancelled')"
    )


# --- MCP Tools ---

@mcp.tool()
async def get_product_sales_details(input_data: GetProductSalesDetailsInput) -> dict:
    """Fetches product details alongside its total units sold and total revenue generated."""
    result = await analytics_repo.get_product_sales_details(
        product_id=input_data.product_id,
        status=input_data.status,
    )
    if not result:
        return {"status": "error", "message": f"Product with ID {input_data.product_id} not found."}

    return {
        "status": "success",
        "data": result,
    }


@mcp.tool()
async def get_sales_by_category(input_data: GetSalesByCategoryInput) -> dict:
    """Groups sales metrics by product category (type) to reveal top-performing categories."""
    category_sales = await analytics_repo.get_sales_by_category(status=input_data.status)
    return {
        "status": "success",
        "count": len(category_sales),
        "data": category_sales,
    }


@mcp.tool()
async def get_overall_merchant_summary() -> dict:
    """Provides a high-level merchant summary: total inventory stock, total successful orders, and overall revenue."""
    summary = await analytics_repo.get_overall_merchant_summary()
    return {
        "status": "success",
        "data": summary,
    }