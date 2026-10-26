import os
import sys
import logging
from typing import Optional, Dict, Any, List
from langchain_core.tools import StructuredTool

# Ensure backend/mcp directory is discoverable for importing FastMCP merchant server
mcp_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp"))
if mcp_path not in sys.path:
    sys.path.insert(0, mcp_path)

try:
    from mcp_server_merchant.server import mcp
except Exception:
    class DummyMCP:
        def tool(self, *args, **kwargs):
            return lambda fn: fn
        def resource(self, *args, **kwargs):
            return lambda fn: fn
    mcp = DummyMCP()

from Merchant.database import merchantRepository
from Product.controller import productController
from Product.schemas import AddProductRequest
from Product.models import ProductType, Product
from Merchant.models import CampaingType
from sqlmodel import select
from config.database import db_connection

logger = logging.getLogger(__name__)

MERCHANT_ONLY_ERROR = (
    "FORBIDDEN: Access denied. This tool is restricted exclusively to verified Dukaan merchants. "
    "Regular customers and unauthorized agents are not permitted to inspect or modify store data."
)


def _check_merchant_authorization(caller_role: Optional[str]) -> bool:
    """Verifies that the tool invocation comes strictly from a merchant role."""
    if not caller_role:
        return False
    clean = str(caller_role).strip().lower()
    return clean in ("merchant", "store_owner", "admin")


# ==============================================================================
# FastMCP Merchant Resources
# ==============================================================================

@mcp.resource("merchant://kpi-definitions")
async def get_merchant_kpi_definitions() -> Dict[str, Any]:
    """Provides key performance indicator formulas and targets for merchant store analytics."""
    return {
        "gross_revenue": "Sum of total order payments received.",
        "net_profit": "Gross revenue minus total cost of goods sold (COGS).",
        "profit_margin_target": "Recommended healthy store margin is 20% to 35%.",
        "stock_alert_threshold": "Low stock warning triggers when units <= 10.",
    }


@mcp.resource("merchant://negotiation-policy")
async def get_merchant_negotiation_policy() -> Dict[str, Any]:
    """Provides storewide guidelines for AI automated discounts in customer chat."""
    policy = await merchantRepository.get_or_create_discount_policy()
    return {
        "max_discount_allowed_percent": policy.max_discount_percentage,
        "min_profit_margin_percent": policy.min_margin_percentage,
        "auto_accept_threshold_percent": policy.auto_accept_threshold,
    }


# ==============================================================================
# Merchant Tools (Strictly Merchant-Only)
# ==============================================================================

@mcp.tool()
async def merchant_get_store_analytics(
    time_range: str = "all",
    caller_role: str = "merchant",
    merchant_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Fetches real-time store performance metrics including gross revenue, net profit,
    overall profit margin %, total orders, units sold, and cumulative discounts given.

    Parameters:
    - time_range (str, Optional, default="all"): Filter window: 'today', '7d', '30d', or 'all'.
    - caller_role (str, Required): Must strictly be 'merchant'. Rejects unauthorized callers.
    - merchant_id (int, Optional): Store owner ID.

    LLM Usage:
    - Call this tool whenever the merchant asks about revenue, profit, margins, sales performance,
      or how much discount has been given.
    """
    if not _check_merchant_authorization(caller_role):
        return {"status": "error", "error": MERCHANT_ONLY_ERROR}

    try:
        data = await merchantRepository.get_dashboard_analytics(time_range=time_range)
        metrics = data.get("metrics", {})
        return {
            "status": "success",
            "time_range": time_range,
            "gross_revenue_inr": metrics.get("total_revenue", 0.0),
            "net_profit_inr": metrics.get("total_profit", 0.0),
            "profit_margin_percent": metrics.get("profit_margin_percent", 0.0),
            "total_orders_count": metrics.get("total_orders", 0),
            "total_items_sold": metrics.get("total_items_sold", 0),
            "average_order_value_inr": metrics.get("average_order_value", 0.0),
            "total_discounts_granted_inr": metrics.get("total_ai_discount_amount", 0.0),
            "average_discount_percent": metrics.get("average_discount_percent", 0.0),
            "active_customers_count": metrics.get("active_customers", 0),
        }
    except Exception as e:
        logger.exception("[MERCHANT TOOL ERROR] merchant_get_store_analytics: %s", e)
        return {"status": "error", "error": f"Failed to retrieve analytics: {str(e)}"}


@mcp.tool()
async def merchant_get_top_selling_products(
    limit: int = 10,
    sort_by: str = "units_sold",
    caller_role: str = "merchant",
) -> Dict[str, Any]:
    """
    Identifies top-performing products in the catalog ranked by units sold, gross revenue,
    or net profit, along with their current inventory stock levels.

    Parameters:
    - limit (int, Optional, default=10): Maximum items to return.
    - sort_by (str, Optional, default="units_sold"): 'units_sold', 'revenue', or 'profit'.
    - caller_role (str, Required): Must strictly be 'merchant'.

    LLM Usage:
    - Use this tool when the merchant asks "which item is selling more", "show top products",
      or "what are my most profitable items".
    """
    if not _check_merchant_authorization(caller_role):
        return {"status": "error", "error": MERCHANT_ONLY_ERROR}

    try:
        data = await merchantRepository.get_dashboard_analytics(time_range="all")
        items = data.get("top_selling_products", [])

        if sort_by == "revenue":
            items.sort(key=lambda x: x.get("total_revenue", 0.0), reverse=True)
        elif sort_by == "profit":
            items.sort(key=lambda x: x.get("total_profit", 0.0), reverse=True)
        else:
            items.sort(key=lambda x: x.get("units_sold", 0), reverse=True)

        sliced = items[:limit]
        return {
            "status": "success",
            "count": len(sliced),
            "top_products": sliced,
        }
    except Exception as e:
        logger.exception("[MERCHANT TOOL ERROR] merchant_get_top_selling_products: %s", e)
        return {"status": "error", "error": f"Failed to fetch top selling products: {str(e)}"}


@mcp.tool()
async def merchant_get_inventory_health_and_reorder_alerts(
    stock_threshold: int = 10,
    caller_role: str = "merchant",
) -> Dict[str, Any]:
    """
    Scans the product catalog and returns items that are out of stock (stock <= 0)
    or low in stock (stock <= stock_threshold) requiring restock orders.

    Parameters:
    - stock_threshold (int, Optional, default=10): Maximum stock count to flag as low stock.
    - caller_role (str, Required): Must strictly be 'merchant'.

    LLM Usage:
    - Use when the merchant asks "what products need restocking", "show low stock items",
      or "inventory health".
    """
    if not _check_merchant_authorization(caller_role):
        return {"status": "error", "error": MERCHANT_ONLY_ERROR}

    try:
        alerts = await merchantRepository.get_inventory_alerts(threshold=stock_threshold)
        out_of_stock = [p for p in alerts if p.get("current_stock", 0) <= 0]
        low_stock = [p for p in alerts if p.get("current_stock", 0) > 0]

        return {
            "status": "success",
            "threshold": stock_threshold,
            "out_of_stock_count": len(out_of_stock),
            "low_stock_count": len(low_stock),
            "critical_items": alerts,
        }
    except Exception as e:
        logger.exception("[MERCHANT TOOL ERROR] merchant_get_inventory_health: %s", e)
        return {"status": "error", "error": f"Failed to check inventory: {str(e)}"}


@mcp.tool()
async def merchant_lookup_order_details(
    order_identifier: str,
    caller_role: str = "merchant",
) -> Dict[str, Any]:
    """
    Looks up full details for any order by either its internal order ID or Razorpay gateway order ID,
    including customer details, line items, prices, margins, and payment status.

    Parameters:
    - order_identifier (str, Required): Order primary ID (e.g. '12') or gateway order ID (e.g. 'order_demo_1001').
    - caller_role (str, Required): Must strictly be 'merchant'.
    """
    if not _check_merchant_authorization(caller_role):
        return {"status": "error", "error": MERCHANT_ONLY_ERROR}

    try:
        clean_id = str(order_identifier).strip()
        all_orders = await merchantRepository.get_all_orders(limit=200)

        match = None
        for ord_dict in all_orders:
            if str(ord_dict.get("id")) == clean_id or str(ord_dict.get("order_id")) == clean_id or str(ord_dict.get("razorpay_order_id")) == clean_id:
                match = ord_dict
                break

        if not match and clean_id.isdigit():
            match = await merchantRepository.get_order_by_id(int(clean_id))

        if not match:
            return {
                "status": "not_found",
                "message": f"No order found matching identifier '{order_identifier}'.",
            }

        return {
            "status": "success",
            "order": match,
        }
    except Exception as e:
        logger.exception("[MERCHANT TOOL ERROR] merchant_lookup_order_details: %s", e)
        return {"status": "error", "error": f"Failed to lookup order: {str(e)}"}


@mcp.tool()
async def merchant_manage_campaign(
    action: str,
    agenda: str = "",
    discount_percentage: float = 0.0,
    priority: int = 1,
    campaign_type: str = "low_priority",
    product_ids: Optional[List[int]] = None,
    campaign_id: Optional[int] = None,
    caller_role: str = "merchant",
) -> Dict[str, Any]:
    """
    Creates, inspects, or deletes marketing campaigns to boost product visibility and drive sales.

    Parameters:
    - action (str, Required): 'create', 'list', 'get', or 'delete'.
    - agenda (str, Optional): Campaign promotion theme/title (e.g., 'Diwali Flash Sale').
    - discount_percentage (float, Optional): Percentage discount linked to the campaign.
    - priority (int, Optional): Numerical priority (1 to 5).
    - campaign_type (str, Optional): 'high_priority', 'medium_priority', or 'low_priority'.
    - product_ids (List[int], Optional): Product IDs to include in the campaign.
    - campaign_id (int, Optional): Target campaign ID for 'get' or 'delete'.
    - caller_role (str, Required): Must strictly be 'merchant'.
    """
    if not _check_merchant_authorization(caller_role):
        return {"status": "error", "error": MERCHANT_ONLY_ERROR}

    try:
        act = action.strip().lower()

        if act == "create":
            if not agenda:
                return {"status": "error", "error": "An agenda title is required to create a campaign."}

            type_enum = CampaingType.LOW_PRIORITY
            if campaign_type in [t.value for t in CampaingType]:
                type_enum = CampaingType(campaign_type)

            camp = await merchantRepository.create_campaign(
                agenda=agenda,
                discount_percentage=discount_percentage,
                priority=priority,
                type=type_enum,
                product_ids=product_ids or [],
            )
            return {
                "status": "success",
                "message": f"Campaign '{camp.agenda}' created with {len(product_ids or [])} linked products.",
                "campaign_id": camp.id,
            }

        elif act == "list":
            campaigns = await merchantRepository.get_all_campaigns()
            return {
                "status": "success",
                "count": len(campaigns),
                "campaigns": campaigns,
            }

        elif act == "get":
            if not campaign_id:
                return {"status": "error", "error": "campaign_id is required for 'get' action."}
            camp = await merchantRepository.get_campaign_by_id(campaign_id)
            if not camp:
                return {"status": "not_found", "message": f"Campaign #{campaign_id} not found."}
            return {"status": "success", "campaign": camp}

        elif act == "delete":
            if not campaign_id:
                return {"status": "error", "error": "campaign_id is required for 'delete' action."}
            ok = await merchantRepository.delete_campaign(campaign_id)
            if not ok:
                return {"status": "not_found", "message": f"Campaign #{campaign_id} not found to delete."}
            return {"status": "success", "message": f"Campaign #{campaign_id} deleted successfully."}

        else:
            return {"status": "error", "error": f"Unknown campaign action '{action}'. Use create, list, get, or delete."}

    except Exception as e:
        logger.exception("[MERCHANT TOOL ERROR] merchant_manage_campaign: %s", e)
        return {"status": "error", "error": f"Campaign operation failed: {str(e)}"}


@mcp.tool()
async def merchant_update_product_pricing_and_margin(
    product_id: int,
    new_price: float,
    cost_price: Optional[float] = None,
    min_profit_margin_percent: Optional[float] = None,
    caller_role: str = "merchant",
) -> Dict[str, Any]:
    """
    Updates a product's public selling price, cost price, and protective minimum profit margin floor.
    Ensures AI agents never negotiate discounts below this margin.

    Parameters:
    - product_id (int, Required): Catalog product ID.
    - new_price (float, Required): New retail selling price in INR.
    - cost_price (float, Optional): New product cost price in INR.
    - min_profit_margin_percent (float, Optional): Minimum acceptable margin floor (e.g. 20.0).
    - caller_role (str, Required): Must strictly be 'merchant'.
    """
    if not _check_merchant_authorization(caller_role):
        return {"status": "error", "error": MERCHANT_ONLY_ERROR}

    try:
        async with db_connection.get_session() as session:
            stmt = select(Product).where(Product.id == product_id)
            res = await session.execute(stmt)
            product = res.scalars().first()
            if not product:
                return {"status": "not_found", "message": f"Product with ID {product_id} not found."}

            old_price = float(product.price)
            product.price = float(new_price)
            if cost_price is not None:
                product.cost_price = float(cost_price)
            if min_profit_margin_percent is not None:
                product.min_profit_margin_percent = float(min_profit_margin_percent)

            session.add(product)
            await session.commit()
            await session.refresh(product)

            return {
                "status": "success",
                "product_id": product.id,
                "name": product.name,
                "old_price": old_price,
                "new_price": float(product.price),
                "cost_price": float(product.cost_price or 0.0),
                "min_profit_margin_percent": float(product.min_profit_margin_percent or 20.0),
                "message": f"Pricing for '{product.name}' updated successfully to ₹{product.price:.2f}.",
            }
    except Exception as e:
        logger.exception("[MERCHANT TOOL ERROR] merchant_update_product_pricing: %s", e)
        return {"status": "error", "error": f"Failed to update pricing: {str(e)}"}


@mcp.tool()
async def merchant_get_customer_negotiation_insights(
    caller_role: str = "merchant",
) -> Dict[str, Any]:
    """
    Provides business intelligence on AI customer bargaining conversations:
    average discount requested by buyers, average discount granted by the AI agent,
    total deal negotiations, and overall chat-to-order conversion rate.

    Parameters:
    - caller_role (str, Required): Must strictly be 'merchant'.
    """
    if not _check_merchant_authorization(caller_role):
        return {"status": "error", "error": MERCHANT_ONLY_ERROR}

    try:
        funnel = await merchantRepository._get_mongo_negotiation_funnel()
        return {
            "status": "success",
            "negotiation_metrics": funnel,
        }
    except Exception as e:
        logger.exception("[MERCHANT TOOL ERROR] merchant_get_customer_negotiation_insights: %s", e)
        return {"status": "error", "error": f"Failed to fetch negotiation insights: {str(e)}"}


@mcp.tool()
async def merchant_publish_catalog_item(
    name: str,
    price: float,
    stock: int,
    product_type: str,
    cost_price: float = 0.0,
    min_profit_margin_percent: float = 20.0,
    brand: str = "Dukaan",
    gender: Optional[str] = None,
    description: Optional[str] = None,
    caller_role: str = "merchant",
) -> Dict[str, Any]:
    """
    Publishes a new garment or product item directly to the storefront catalog.

    Parameters:
    - name (str, Required): Product name.
    - price (float, Required): Retail price in INR.
    - stock (int, Required): Stock inventory quantity.
    - product_type (str, Required): Category: 't-shirt', 'short', 'shirt', 'hoodie', 'jeans'.
    - cost_price (float, Optional, default=0.0): Merchant manufacturing/procurement cost.
    - min_profit_margin_percent (float, Optional, default=20.0): Floor margin % for bargaining.
    - brand (str, Optional, default="Dukaan"): Brand label.
    - gender (str, Optional): 'Men', 'Women', or 'Unisex'.
    - description (str, Optional): Product description.
    - caller_role (str, Required): Must strictly be 'merchant'.
    """
    if not _check_merchant_authorization(caller_role):
        return {"status": "error", "error": MERCHANT_ONLY_ERROR}

    try:
        clean_type = product_type.strip().lower()
        valid_types = [t.value for t in ProductType]
        if clean_type not in valid_types:
            return {
                "status": "error",
                "error": f"Invalid product_type '{product_type}'. Allowed types: {valid_types}",
            }

        payload = AddProductRequest(
            name=name,
            price=price,
            stock=stock,
            type=ProductType(clean_type),
            gender=gender,
            brand=brand,
            cost_price=cost_price,
            description=description,
            min_profit_margin_percent=min_profit_margin_percent,
        )

        created = await productController.add_product(payload=payload, merchant_id=1)
        return {
            "status": "success",
            "message": f"Product '{created.name}' published successfully.",
            "product_id": created.id,
            "data": created.model_dump() if hasattr(created, "model_dump") else created,
        }
    except Exception as e:
        logger.exception("[MERCHANT TOOL ERROR] merchant_publish_catalog_item: %s", e)
        return {"status": "error", "error": f"Failed to publish catalog item: {str(e)}"}


# ==============================================================================
# LangChain / LangGraph Adapter Helper
# ==============================================================================

def get_merchant_langchain_tools() -> List[StructuredTool]:
    """
    Returns all merchant administration and analytics tools wrapped as native
    LangChain StructuredTools, ready to bind directly to the Merchant Agent.
    """
    return [
        StructuredTool.from_function(
            coroutine=merchant_get_store_analytics,
            name="merchant_get_store_analytics",
            description=merchant_get_store_analytics.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=merchant_get_top_selling_products,
            name="merchant_get_top_selling_products",
            description=merchant_get_top_selling_products.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=merchant_get_inventory_health_and_reorder_alerts,
            name="merchant_get_inventory_health_and_reorder_alerts",
            description=merchant_get_inventory_health_and_reorder_alerts.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=merchant_lookup_order_details,
            name="merchant_lookup_order_details",
            description=merchant_lookup_order_details.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=merchant_manage_campaign,
            name="merchant_manage_campaign",
            description=merchant_manage_campaign.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=merchant_update_product_pricing_and_margin,
            name="merchant_update_product_pricing_and_margin",
            description=merchant_update_product_pricing_and_margin.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=merchant_get_customer_negotiation_insights,
            name="merchant_get_customer_negotiation_insights",
            description=merchant_get_customer_negotiation_insights.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=merchant_publish_catalog_item,
            name="merchant_publish_catalog_item",
            description=merchant_publish_catalog_item.__doc__,
        ),
    ]
