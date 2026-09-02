from typing import Optional, List, Dict, Any
from sqlmodel import select
from sqlalchemy import func
from config.database import db_connection
from models import Product, Order, ProductType

class AnalyticsRepository:
    
    async def get_product_sales_details(self, product_id: int, status: str = "completed") -> Optional[Dict[str, Any]]:
        """
        Fetches full product details alongside its total sales count and total revenue generated.
        Filters by order status (default: 'completed').
        """
        async with db_connection.get_session() as session:
            # Fetch the base product details
            product = (await session.exec(select(Product).where(Product.id == product_id))).first()
            
            if not product:
                return None
                
            # Perform the cross-table aggregation
            sales_query = (
                select(
                    func.count(Order.id).label("total_sold"),
                    func.sum(Product.price - Order.discount_applied).label("total_revenue")
                )
                .join(Product, Order.product_id == Product.id)
                .where(Order.product_id == product_id)
                # Ensure we only count actual sales, not pending carts
                .where(Order.status == status) 
            )
            
            sales_result = await session.exec(sales_query)
            sales_data = sales_result.first()
            
            return {
                "product_details": product.model_dump(),
                "analytics": {
                    "total_units_sold": sales_data.total_sold or 0,
                    "total_revenue_generated": sales_data.total_revenue or 0.0
                }
            }

    async def get_sales_by_category(self, status: str = "completed") -> List[Dict[str, Any]]:
        """
        Groups sales by Product Category (Type) to show which categories are selling best.
        """
        async with db_connection.get_session() as session:
            query = (
                select(
                    Product.type,
                    func.count(Order.id).label("total_sold"),
                    func.sum(Product.price - Order.discount_applied).label("total_revenue")
                )
                .join(Order, Order.product_id == Product.id)
                .where(Order.status == status)
                .group_by(Product.type)
                .order_by(func.count(Order.id).desc()) # Order by most sold
            )
            
            result = await session.exec(query)
            rows = result.all()
            
            return [
                {
                    "category": row.type,
                    "total_units_sold": row.total_sold,
                    "total_revenue": round(row.total_revenue or 0.0, 2)
                }
                for row in rows
            ]

    async def get_overall_merchant_summary(self) -> Dict[str, Any]:
        """
        Provides a high-level overview: Total products, Total Sales, and Overall Revenue.
        """
        async with db_connection.get_session() as session:
            # 1. Total products in inventory
            total_inventory = (await session.exec(select(func.sum(Product.stock)))).first() or 0
            
            # 2. Total successful orders & revenue
            sales_query = (
                select(
                    func.count(Order.id).label("total_orders"),
                    func.sum(Product.price - Order.discount_applied).label("total_revenue")
                )
                .join(Product, Order.product_id == Product.id)
                .where(Order.status == "completed")
            )
            sales_result = (await session.exec(sales_query)).first()

            return {
                "total_inventory_items": total_inventory,
                "total_successful_orders": sales_result.total_orders or 0,
                "total_overall_revenue": round(sales_result.total_revenue or 0.0, 2)
            }