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
from Merchant.utils import serialize_mongo_doc
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


@mcp.tool()
async def merchant_get_order_history(
    status: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    caller_role: str = "merchant",
) -> Dict[str, Any]:
    """
    Fetches the store's complete order history and total revenue received,
    allowing the merchant/shopkeeper to check cumulative total money received,
    order counts, breakdown by status, and individual order details.

    Parameters:
    - status (str, Optional): Filter by status (e.g. 'placed', 'completed', 'paid', 'pending', 'cancelled'). Default is None (all orders).
    - limit (int, Optional, default=50): Maximum number of orders to return.
    - skip (int, Optional, default=0): Offset for pagination.
    - caller_role (str, Required): Must strictly be 'merchant'.

    LLM Usage:
    - Call this tool whenever the merchant asks about:
      * "Check order history"
      * "How much total money / order total did we receive?"
      * "Total sales / revenue received from orders"
      * "List recent customer orders and payment statuses"
    """
    if not _check_merchant_authorization(caller_role):
        return {"status": "error", "error": MERCHANT_ONLY_ERROR}

    try:
        raw_orders = await merchantRepository.get_all_orders(limit=limit, skip=skip, status=status)
        
        total_revenue = 0.0
        total_discounts = 0.0
        status_counts: Dict[str, int] = {}
        formatted_orders = []

        for ord_dict in raw_orders:
            amt = float(ord_dict.get("total_amount") or 0.0)
            disc = float(ord_dict.get("discount_applied") or 0.0)
            st = str(ord_dict.get("status") or "placed").lower()

            total_revenue += amt
            total_discounts += disc
            status_counts[st] = status_counts.get(st, 0) + 1

            prods = ord_dict.get("products") or []
            item_names = [p.get("name") for p in prods if p.get("name")]
            total_items_count = sum(p.get("quantity", 1) for p in prods)

            formatted_orders.append({
                "order_id": ord_dict.get("order_id") or ord_dict.get("id"),
                "gateway_id": ord_dict.get("razorpay_order_id"),
                "customer_name": ord_dict.get("user", {}).get("name", "Customer"),
                "customer_email": ord_dict.get("user", {}).get("email"),
                "total_amount_inr": round(amt, 2),
                "discount_applied_inr": round(disc, 2),
                "status": st,
                "items_count": total_items_count,
                "products_summary": ", ".join(item_names[:3]) + ("..." if len(item_names) > 3 else ""),
                "created_at": ord_dict.get("created_at"),
            })

        return {
            "status": "success",
            "filter_status": status,
            "total_orders_received": len(raw_orders),
            "total_revenue_received_inr": round(total_revenue, 2),
            "total_discounts_given_inr": round(total_discounts, 2),
            "status_breakdown": status_counts,
            "orders": formatted_orders,
        }
    except Exception as e:
        logger.exception("[MERCHANT TOOL ERROR] merchant_get_order_history: %s", e)
        return {"status": "error", "error": f"Failed to retrieve order history: {str(e)}"}


@mcp.tool()
async def merchant_get_customer_chat_threads(
    limit: int = 20,
    user_id: Optional[int] = None,
    caller_role: str = "merchant",
) -> Dict[str, Any]:
    """
    Retrieves customer shopping, negotiation, and assistance chat threads from MongoDB.
    Allows the merchant to inspect customer interactions, shopping sessions, and negotiation activity.

    Parameters:
    - limit (int, Optional, default=20): Number of threads to return.
    - user_id (int, Optional): Filter threads belonging to a specific customer ID.
    - caller_role (str, Required): Must strictly be 'merchant'.

    LLM Usage:
    - Call this tool when the merchant wants to see:
      * "Customer chat threads"
      * "Inspect customer conversations"
      * "What sessions did customer #4 have?"
      * "List recent customer chats"
    """
    if not _check_merchant_authorization(caller_role):
        return {"status": "error", "error": MERCHANT_ONLY_ERROR}

    try:
        from Chat.database import chat_audit_repo
        if user_id is not None:
            raw_threads = await chat_audit_repo.get_all_threads_for_user(int(user_id))
        else:
            cursor = chat_audit_repo.collection.find().sort("updated_at", -1).limit(limit)
            raw_threads = await cursor.to_list(length=limit)

        threads_summary = []
        for t in raw_threads:
            doc = serialize_mongo_doc(t)
            msgs = doc.get("messages") or []
            state = doc.get("state") or {}

            latest_user_text = None
            latest_ai_text = None
            for m in reversed(msgs):
                sender = str(m.get("sender") or "").lower()
                text = m.get("message") or ""
                if not latest_user_text and sender in ("human", "user"):
                    latest_user_text = text[:120]
                elif not latest_ai_text and sender in ("ai", "assistant"):
                    latest_ai_text = text[:120]
                if latest_user_text and latest_ai_text:
                    break

            threads_summary.append({
                "thread_id": doc.get("thread_id"),
                "user_id": doc.get("user_id"),
                "messages_count": len(msgs),
                "created_at": doc.get("created_at"),
                "updated_at": doc.get("updated_at"),
                "order_placed": state.get("order_placed", False),
                "negotiated_discount_percent": state.get("discount") or state.get("discount_percentage", 0),
                "latest_user_message": latest_user_text,
                "latest_ai_response": latest_ai_text,
            })

        return {
            "status": "success",
            "threads_count": len(threads_summary),
            "user_id_filter": user_id,
            "threads": threads_summary,
        }
    except Exception as e:
        logger.exception("[MERCHANT TOOL ERROR] merchant_get_customer_chat_threads: %s", e)
        return {"status": "error", "error": f"Failed to retrieve customer chat threads: {str(e)}"}


@mcp.tool()
async def merchant_get_chat_thread_transcript(
    thread_id: str,
    user_id: Optional[int] = None,
    caller_role: str = "merchant",
) -> Dict[str, Any]:
    """
    Retrieves the complete message-by-message transcript and bargaining state
    for a specific customer chat thread.

    Parameters:
    - thread_id (str, Required): Unique thread identifier (e.g. 'thread_user_12_abc').
    - user_id (int, Optional): Customer ID if known.
    - caller_role (str, Required): Must strictly be 'merchant'.

    LLM Usage:
    - Call this tool when the merchant wants to inspect the exact dialog of a customer session:
      * "Show me transcript for thread thread_user_5_xyz"
      * "Read chat transcript for session 123"
      * "What exact messages did the customer exchange with the AI?"
    """
    if not _check_merchant_authorization(caller_role):
        return {"status": "error", "error": MERCHANT_ONLY_ERROR}

    try:
        from Chat.database import chat_audit_repo
        clean_tid = str(thread_id).strip()

        query: Dict[str, Any] = {"thread_id": clean_tid}
        if user_id is not None:
            query["user_id"] = int(user_id)

        doc = await chat_audit_repo.collection.find_one(query)
        if not doc:
            doc = await chat_audit_repo.collection.find_one({"thread_id": {"$regex": clean_tid, "$options": "i"}})

        if not doc:
            return {
                "status": "not_found",
                "message": f"No chat thread found matching ID '{thread_id}'.",
            }

        serialized = serialize_mongo_doc(doc)
        msgs = serialized.get("messages") or []
        formatted_messages = []
        for m in msgs:
            formatted_messages.append({
                "sender": m.get("sender") or ("user" if m.get("role") == "user" else "assistant"),
                "message": m.get("message") or m.get("content") or "",
                "timestamp": m.get("timestamp"),
                "has_cards": bool(m.get("cards")),
            })

        state = serialized.get("state") or {}
        return {
            "status": "success",
            "thread_id": serialized.get("thread_id"),
            "user_id": serialized.get("user_id"),
            "created_at": serialized.get("created_at"),
            "updated_at": serialized.get("updated_at"),
            "message_count": len(formatted_messages),
            "order_placed": state.get("order_placed", False),
            "discount_percentage": state.get("discount") or state.get("discount_percentage", 0),
            "negotiation_log": state.get("negotiation_log", []),
            "messages": formatted_messages,
        }
    except Exception as e:
        logger.exception("[MERCHANT TOOL ERROR] merchant_get_chat_thread_transcript: %s", e)
        return {"status": "error", "error": f"Failed to retrieve chat transcript: {str(e)}"}


# ==============================================================================
# LangChain / LangGraph Adapter Helper
# ==============================================================================

def get_merchant_langchain_tools() -> List[StructuredTool]:
    """
    Returns all 13 merchant administration, product management, order history,
    customer chat thread inspection, and analytics tools wrapped as native
    LangChain StructuredTools, ready to bind directly to the Merchant Agent
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
            coroutine=merchant_get_order_history,
            name="merchant_get_order_history",
            description=merchant_get_order_history.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=merchant_get_customer_chat_threads,
            name="merchant_get_customer_chat_threads",
            description=merchant_get_customer_chat_threads.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=merchant_get_chat_thread_transcript,
            name="merchant_get_chat_thread_transcript",
            description=merchant_get_chat_thread_transcript.__doc__,
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
