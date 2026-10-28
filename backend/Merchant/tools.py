import os
import sys
import logging
from typing import Optional, Dict, Any, List
from langchain_core.tools import StructuredTool

# Ensure backend root is discoverable for importing FastMCP merchant server
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

try:
    from mcp.merchant.server import mcp
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
# Native Merchant Function Tools (Strictly Merchant-Only)
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
                "message": f"Pricing for '{product.name}' updated successfully to INR {product.price:.2f}.",
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
    sizes: Optional[str] = None,
    discount: int = 0,
    image_url: Optional[str] = None,
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
    - sizes (str, Optional): Comma-separated sizes (e.g. 'S,M,L,XL').
    - discount (int, Optional, default=0): Initial discount percentage (0-100).
    - image_url (str, Optional): Product image URL.
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
            sizes=sizes,
            discount=discount,
            image_url=image_url,
            min_profit_margin_percent=min_profit_margin_percent,
        )

        created_res = await productController.add_product(product=payload)
        created = created_res.get("product") if isinstance(created_res, dict) else created_res
        prod_id = getattr(created, "id", None) or (created.get("id") if isinstance(created, dict) else None)
        prod_name = getattr(created, "name", name) or name

        return {
            "status": "success",
            "message": f"Product '{prod_name}' published successfully.",
            "product_id": prod_id,
            "data": created.model_dump() if hasattr(created, "model_dump") else created,
        }
    except Exception as e:
        logger.exception("[MERCHANT TOOL ERROR] merchant_publish_catalog_item: %s", e)
        return {"status": "error", "error": f"Failed to publish catalog item: {str(e)}"}


# Alias for intuitive LLM tool calling
merchant_add_product = merchant_publish_catalog_item


@mcp.tool()
async def merchant_edit_product_details(
    product_id: int,
    name: Optional[str] = None,
    price: Optional[float] = None,
    stock: Optional[int] = None,
    product_type: Optional[str] = None,
    cost_price: Optional[float] = None,
    min_profit_margin_percent: Optional[float] = None,
    brand: Optional[str] = None,
    gender: Optional[str] = None,
    description: Optional[str] = None,
    sizes: Optional[str] = None,
    discount: Optional[int] = None,
    image_url: Optional[str] = None,
    caller_role: str = "merchant",
) -> Dict[str, Any]:
    """
    Edits and updates details of an existing catalog product:
    name, retail price, stock inventory quantity, product category, cost price,
    minimum profit margin percentage floor, brand, gender, description, sizes, discount %, and image URL.

    Parameters:
    - product_id (int, Required): Catalog product ID to update.
    - name (str, Optional): New product name.
    - price (float, Optional): New retail selling price in INR.
    - stock (int, Optional): Updated stock quantity.
    - product_type (str, Optional): Category: 't-shirt', 'short', 'shirt', 'hoodie', 'jeans'.
    - cost_price (float, Optional): Manufacturing or wholesale procurement cost in INR.
    - min_profit_margin_percent (float, Optional): Floor margin percentage for AI bargaining.
    - brand (str, Optional): Brand label.
    - gender (str, Optional): Target gender: 'Men', 'Women', or 'Unisex'.
    - description (str, Optional): Detailed product description.
    - sizes (str, Optional): Comma-separated sizes (e.g. 'S,M,L,XL').
    - discount (int, Optional): Public listing discount percentage (0-100).
    - image_url (str, Optional): URL of the product image.
    - caller_role (str, Required): Must strictly be 'merchant'.
    """
    if not _check_merchant_authorization(caller_role):
        return {"status": "error", "error": MERCHANT_ONLY_ERROR}

    try:
        update_data = {}
        if name is not None:
            update_data["name"] = name.strip()
        if price is not None:
            update_data["price"] = float(price)
        if stock is not None:
            update_data["stock"] = int(stock)
        if product_type is not None:
            clean_type = product_type.strip().lower()
            valid_types = [t.value for t in ProductType]
            if clean_type not in valid_types:
                return {
                    "status": "error",
                    "error": f"Invalid product_type '{product_type}'. Allowed types: {valid_types}",
                }
            update_data["type"] = ProductType(clean_type)
        if cost_price is not None:
            update_data["cost_price"] = float(cost_price)
        if min_profit_margin_percent is not None:
            update_data["min_profit_margin_percent"] = float(min_profit_margin_percent)
        if brand is not None:
            update_data["brand"] = brand.strip()
        if gender is not None:
            update_data["gender"] = gender.strip()
        if description is not None:
            update_data["description"] = description.strip()
        if sizes is not None:
            update_data["sizes"] = sizes.strip()
        if discount is not None:
            update_data["discount"] = int(discount)
        if image_url is not None:
            update_data["image_url"] = image_url.strip()

        if not update_data:
            return {
                "status": "error",
                "error": "No update fields were provided. Specify at least one field to edit (name, price, stock, etc.).",
            }

        res = await productController.update_product(product_id=product_id, payload=update_data)
        updated = res.get("product") if isinstance(res, dict) else res

        return {
            "status": "success",
            "message": f"Product #{product_id} updated successfully.",
            "product_id": product_id,
            "updated_fields": list(update_data.keys()),
            "data": updated.model_dump() if hasattr(updated, "model_dump") else updated,
        }
    except Exception as e:
        logger.exception("[MERCHANT TOOL ERROR] merchant_edit_product_details: %s", e)
        return {"status": "error", "error": f"Failed to update product #{product_id}: {str(e)}"}


# Alias
merchant_update_product_details = merchant_edit_product_details


@mcp.tool()
async def merchant_get_product_details(
    product_id: int,
    caller_role: str = "merchant",
) -> Dict[str, Any]:
    """
    Retrieves complete details of a specific product from the catalog by its product ID:
    name, retail price, cost price, inventory stock, profit margin floor,
    category, brand, gender, sizes, and discount.

    Parameters:
    - product_id (int, Required): Catalog product ID.
    - caller_role (str, Required): Must strictly be 'merchant'.
    """
    if not _check_merchant_authorization(caller_role):
        return {"status": "error", "error": MERCHANT_ONLY_ERROR}

    try:
        res = await productController.get_by_id(product_id=product_id)
        prod = res.get("product") if isinstance(res, dict) else res
        if not prod:
            return {"status": "not_found", "message": f"Product #{product_id} not found."}

        prod_data = prod.model_dump() if hasattr(prod, "model_dump") else prod
        return {
            "status": "success",
            "product_id": product_id,
            "product": prod_data,
        }
    except Exception as e:
        logger.exception("[MERCHANT TOOL ERROR] merchant_get_product_details: %s", e)
        return {"status": "error", "error": f"Failed to retrieve product #{product_id}: {str(e)}"}


@mcp.tool()
async def merchant_delete_product(
    product_id: int,
    caller_role: str = "merchant",
) -> Dict[str, Any]:
    """
    Deletes or removes a product from the storefront catalog by its product ID.

    Parameters:
    - product_id (int, Required): Catalog product ID to delete.
    - caller_role (str, Required): Must strictly be 'merchant'.
    """
    if not _check_merchant_authorization(caller_role):
        return {"status": "error", "error": MERCHANT_ONLY_ERROR}

    try:
        res = await productController.delete_product(product_id=product_id)
        return {
            "status": "success",
            "message": f"Product #{product_id} deleted successfully.",
            "product_id": product_id,
        }
    except Exception as e:
        logger.exception("[MERCHANT TOOL ERROR] merchant_delete_product: %s", e)
        return {"status": "error", "error": f"Failed to delete product #{product_id}: {str(e)}"}


# ==============================================================================
# LangChain / LangGraph Adapter Helper
# ==============================================================================

def get_merchant_langchain_tools() -> List[StructuredTool]:
    """
    Returns all 10 merchant administration, product management, and analytics tools
    wrapped as native LangChain StructuredTools, ready to bind directly to the Merchant Agent
    with ZERO external MCP server dependency.
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
        StructuredTool.from_function(
            coroutine=merchant_edit_product_details,
            name="merchant_edit_product_details",
            description=merchant_edit_product_details.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=merchant_get_product_details,
            name="merchant_get_product_details",
            description=merchant_get_product_details.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=merchant_delete_product,
            name="merchant_delete_product",
            description=merchant_delete_product.__doc__,
        ),
    ]
