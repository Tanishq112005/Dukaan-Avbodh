from sqlmodel import select
from sqlalchemy.orm import selectinload
from config.database import db_connection
from models import Order, Product
from datetime import datetime
from collections import defaultdict

class AnalyticsService:
    @staticmethod
    async def get_dashboard_metrics():
        async with db_connection.get_session() as session:
            statement = select(Order).options(selectinload(Order.product)).where(Order.status == "confirmed")
            results = await session.execute(statement)
            orders = results.scalars().all()

            total_revenue = 0.0
            total_cost = 0.0
            total_ai_discount_amount = 0.0
            total_original_revenue = 0.0
            
            category_data = defaultdict(lambda: {"revenue": 0.0, "profit": 0.0, "count": 0})
            trend_data = defaultdict(lambda: {"revenue": 0.0, "profit": 0.0, "discount_given": 0.0})

            for order in orders:
                if not order.product:
                    continue
                    
                original_price = float(order.product.price)
                discount_percent = float(order.discount_applied) if order.discount_applied else 0.0
                cost = float(order.product.cost_price)
                
                discount_amount = original_price * (discount_percent / 100.0)
                final_price = original_price - discount_amount
                profit = final_price - cost
                
                # Global metrics
                total_original_revenue += original_price
                total_revenue += final_price
                total_cost += cost
                total_ai_discount_amount += discount_amount
                
                # Category breakdown
                cat = order.product.type.value
                category_data[cat]["revenue"] += final_price
                category_data[cat]["profit"] += profit
                category_data[cat]["count"] += 1
                
                # Date trend
                date_str = order.created_at.strftime("%Y-%m-%d")
                trend_data[date_str]["revenue"] += final_price
                trend_data[date_str]["profit"] += profit
                trend_data[date_str]["discount_given"] += discount_amount
                
            total_profit = total_revenue - total_cost
            avg_profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
            
            # Format outputs
            formatted_category = []
            for cat, data in category_data.items():
                formatted_category.append({
                    "name": cat,
                    "revenue": round(data["revenue"], 2),
                    "profit": round(data["profit"], 2),
                    "sales": data["count"]
                })
                
            # Sort trends by date
            formatted_trend = []
            for date_str in sorted(trend_data.keys()):
                data = trend_data[date_str]
                formatted_trend.append({
                    "date": date_str,
                    "revenue": round(data["revenue"], 2),
                    "profit": round(data["profit"], 2),
                    "discount_given": round(data["discount_given"], 2)
                })
                
            return {
                "metrics": {
                    "total_revenue": round(total_revenue, 2),
                    "total_profit": round(total_profit, 2),
                    "profit_margin_percent": round(avg_profit_margin, 2),
                    "total_ai_discount_amount": round(total_ai_discount_amount, 2),
                    "total_orders": len(orders)
                },
                "revenue_by_category": formatted_category,
                "revenue_trend": formatted_trend
            }

analytics_service = AnalyticsService()
