import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status
from User.models import UserRole

logger = logging.getLogger(__name__)


def resolve_time_range(time_range: str) -> Optional[datetime]:
    """
    Computes the cutoff datetime for dashboard analytics queries based on time range string:
    'today' -> start of today (00:00:00)
    '7d'    -> exactly 7 days ago
    '30d'   -> exactly 30 days ago
    'all'   -> None (no lower bound cutoff)
    """
    now = datetime.now()
    clean_tr = (time_range or "all").strip().lower()

    if clean_tr == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif clean_tr in ("7d", "7days", "week"):
        return now - timedelta(days=7)
    elif clean_tr in ("30d", "30days", "month"):
        return now - timedelta(days=30)
    elif clean_tr in ("all", "all_time", "lifetime"):
        return None
    else:
        # Default fallback to all-time
        return None


def calculate_profit_margin(revenue: float, cost: float) -> float:
    """Calculates net profit margin percentage safely preventing ZeroDivisionError."""
    if revenue <= 0:
        return 0.0
    profit = revenue - cost
    return round((profit / revenue) * 100.0, 1)


def calculate_discount_amount(original_price: float, discount_percent: float) -> float:
    """Calculates absolute monetary discount given from original price and percentage."""
    if original_price <= 0 or discount_percent <= 0:
        return 0.0
    return round(original_price * (discount_percent / 100.0), 2)


def get_stock_status(stock: Optional[int]) -> str:
    """Returns catalog inventory categorization for stock counts."""
    qty = stock if stock is not None else 0
    if qty <= 0:
        return "Out of Stock"
    elif qty <= 10:
        return "Low Stock"
    return "In Stock"


def format_inr_currency(amount: float) -> str:
    """Formats float number as Indian Rupee string."""
    return f"₹{amount:,.2f}"


def serialize_mongo_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively transforms MongoDB ObjectId and datetime instances
    into JSON-serializable strings.
    """
    if not isinstance(doc, dict):
        return doc

    cleaned = {}
    for key, value in doc.items():
        if key == "_id":
            cleaned["_id"] = str(value)
        elif isinstance(value, datetime):
            cleaned[key] = value.isoformat()
        elif isinstance(value, dict):
            cleaned[key] = serialize_mongo_doc(value)
        elif isinstance(value, list):
            cleaned[key] = [
                serialize_mongo_doc(item) if isinstance(item, dict)
                else (item.isoformat() if isinstance(item, datetime) else item)
                for item in value
            ]
        else:
            cleaned[key] = value

    return cleaned


def verify_merchant_role(current_user: Optional[Dict[str, Any]]) -> bool:
    """Checks whether the user dict contains the verified merchant role."""
    if not current_user or not isinstance(current_user, dict):
        return False
    role = current_user.get("role")
    return role == UserRole.MERCHANT.value or role == "merchant"


def assert_merchant_access(current_user: Optional[Dict[str, Any]]) -> None:
    """
    Enforces that caller is authenticated with merchant privileges.
    Raises HTTPException 403 Forbidden otherwise.
    """
    if not verify_merchant_role(current_user):
        user_role = current_user.get("role") if current_user else "unauthenticated"
        logger.warning("[MERCHANT ACCESS DENIED] Unauthorized role attempt: %s", user_role)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied — merchant privileges required. Current role: {user_role}",
        )
