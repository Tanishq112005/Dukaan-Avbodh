from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AnalyticsTimeRange(str, Enum):
    TODAY = "today"
    SEVEN_DAYS = "7d"
    THIRTY_DAYS = "30d"
    ALL = "all"


# ==============================================================================
# Dashboard Analytics Schemas
# ==============================================================================

class KpiMetrics(BaseModel):
    total_revenue: float = Field(default=0.0, description="Gross total revenue in INR")
    total_profit: float = Field(default=0.0, description="Net store profit in INR")
    profit_margin_percent: float = Field(default=0.0, description="Storewide average profit margin percentage")
    total_orders: int = Field(default=0, description="Total count of valid completed/shipped/placed orders")
    total_items_sold: int = Field(default=0, description="Total units of products purchased")
    average_order_value: float = Field(default=0.0, description="Average monetary basket value per order")
    total_ai_discount_amount: float = Field(default=0.0, description="Cumulative monetary discounts granted via AI")
    average_discount_percent: float = Field(default=0.0, description="Average percentage discount applied")
    active_customers: int = Field(default=0, description="Unique customer user count")


class TopSellingProductItem(BaseModel):
    product_id: int
    name: str
    brand: str = "Dukaan"
    category: str
    image_url: Optional[str] = None
    price: float
    cost_price: float = 0.0
    units_sold: int = 0
    total_revenue: float = 0.0
    total_profit: float = 0.0
    current_stock: int = 0
    stock_status: str = "In Stock"


class InventoryAlertItem(BaseModel):
    product_id: int
    name: str
    brand: str = "Dukaan"
    category: str
    current_stock: int
    price: float
    image_url: Optional[str] = None
    status: str = "Low Stock"


class CategoryRevenueItem(BaseModel):
    name: str
    revenue: float = 0.0
    profit: float = 0.0
    sales: int = 0
    share_percent: float = 0.0
    margin_percent: float = 0.0


class RevenueTrendItem(BaseModel):
    date: str
    revenue: float = 0.0
    profit: float = 0.0
    discount_given: float = 0.0
    orders: int = 0


class NegotiationAnalytics(BaseModel):
    total_chat_sessions: int = 0
    total_negotiation_rounds: int = 0
    agreed_deals_count: int = 0
    average_discount_requested: float = 0.0
    average_discount_granted: float = 0.0
    conversion_rate: float = 0.0
    orders_placed_from_chat: int = 0


class MerchantDashboardAnalyticsResponse(BaseModel):
    time_range: str
    metrics: KpiMetrics
    top_selling_products: List[TopSellingProductItem] = Field(default_factory=list)
    inventory_alerts: List[InventoryAlertItem] = Field(default_factory=list)
    revenue_by_category: List[CategoryRevenueItem] = Field(default_factory=list)
    revenue_trend: List[RevenueTrendItem] = Field(default_factory=list)
    negotiation_analytics: NegotiationAnalytics = Field(default_factory=NegotiationAnalytics)


# ==============================================================================
# Orders Schemas
# ==============================================================================

class MerchantOrderUser(BaseModel):
    id: Optional[int] = None
    name: str = "Customer"
    email: str = "customer@dukaan.local"
    address: str = "Bangalore, India"


class MerchantOrderProduct(BaseModel):
    id: int
    name: str
    image_url: Optional[str] = None
    price: float
    cost_price: float = 0.0
    brand: str = "Dukaan"
    quantity: int = 1


class MerchantOrderResponseItem(BaseModel):
    id: str
    order_id: int
    status: str
    payment_status: str
    discount_applied: float = 0.0
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    total_amount: float = 0.0
    created_at: Optional[str] = None
    products: List[MerchantOrderProduct] = Field(default_factory=list)
    user: MerchantOrderUser = Field(default_factory=MerchantOrderUser)


class MerchantOrdersResponse(BaseModel):
    orders: List[MerchantOrderResponseItem] = Field(default_factory=list)


class UpdateOrderStatusRequest(BaseModel):
    status: str = Field(..., description="Target status, e.g. 'paid', 'shipped', 'delivered', 'cancelled'")


# ==============================================================================
# Audit Logs & Chat Threads Schemas
# ==============================================================================

class AuditLogsResponse(BaseModel):
    logs: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None


class ChatThreadsResponse(BaseModel):
    threads: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None


# ==============================================================================
# Merchant Chat & Pricing Bounds Schemas
# ==============================================================================

class MerchantChatRequest(BaseModel):
    text: str = Field(..., description="Message text or analytical query from merchant")
    thread_id: Optional[str] = Field(default=None, description="Optional thread session ID")


class MerchantChatResponse(BaseModel):
    type: str = "merchant_chat_reply"
    message: str
    thread_id: Optional[str] = None
    state: Optional[Dict[str, Any]] = None


class PricingBoundsUpdateRequest(BaseModel):
    max_discount_percentage: Optional[float] = Field(default=25.0, ge=0.0, le=90.0)
    min_margin_percentage: Optional[float] = Field(default=15.0, ge=0.0, le=90.0)
    auto_accept_threshold: Optional[float] = Field(default=10.0, ge=0.0, le=50.0)
