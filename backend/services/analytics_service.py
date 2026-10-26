import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional, List, Dict, Any
from sqlmodel import select
from sqlalchemy.orm import joinedload

from config.database import db_connection
from Order.models import Order
from Product.models import Product
from User.models import User

logger = logging.getLogger(__name__)


class AnalyticsService:
    @staticmethod
    async def _ensure_seed_orders_if_empty(session):
        """
        If the orders table is empty (e.g. in development or fresh deployment),
        seeds realistic sample orders linked to existing catalog products and users
        so the merchant analytics dashboard reflects actionable sales and revenue data.
        """
        try:
            order_check = await session.execute(select(Order).limit(1))
            if order_check.scalars().first():
                return  # Orders already exist

            # Fetch existing products and users
            prods_res = await session.execute(select(Product).limit(30))
            products = prods_res.scalars().all()
            if not products:
                return

            users_res = await session.execute(select(User).limit(5))
            users = users_res.scalars().all()
            default_user_id = users[0].id if users else 1

            now = datetime.now()
            # 14-day realistic distribution of order history
            sample_data = [
                {"prod_idx": 0, "qty": 4, "discount": 8.0, "days_ago": 13, "status": "delivered"},
                {"prod_idx": 1, "qty": 2, "discount": 5.0, "days_ago": 12, "status": "delivered"},
                {"prod_idx": 2, "qty": 5, "discount": 10.0, "days_ago": 11, "status": "delivered"},
                {"prod_idx": 0, "qty": 3, "discount": 6.0, "days_ago": 10, "status": "delivered"},
                {"prod_idx": 3, "qty": 2, "discount": 4.0, "days_ago": 9, "status": "delivered"},
                {"prod_idx": 4, "qty": 6, "discount": 12.0, "days_ago": 8, "status": "delivered"},
                {"prod_idx": 1, "qty": 3, "discount": 5.0, "days_ago": 7, "status": "delivered"},
                {"prod_idx": 5, "qty": 4, "discount": 7.0, "days_ago": 6, "status": "delivered"},
                {"prod_idx": 2, "qty": 3, "discount": 8.0, "days_ago": 5, "status": "delivered"},
                {"prod_idx": 6, "qty": 2, "discount": 0.0, "days_ago": 4, "status": "shipped"},
                {"prod_idx": 0, "qty": 5, "discount": 10.0, "days_ago": 3, "status": "shipped"},
                {"prod_idx": 7, "qty": 3, "discount": 5.0, "days_ago": 2, "status": "processing"},
                {"prod_idx": 3, "qty": 4, "discount": 6.0, "days_ago": 1, "status": "processing"},
                {"prod_idx": 1, "qty": 4, "discount": 8.0, "days_ago": 0, "status": "paid"},
                {"prod_idx": 4, "qty": 3, "discount": 5.0, "days_ago": 0, "status": "paid"},
            ]

            for i, item in enumerate(sample_data):
                p = products[item["prod_idx"] % len(products)]
                u_id = users[i % len(users)].id if users else default_user_id
                price = float(p.price)
                discount_pct = float(item["discount"])
                final_item_price = price * (1.0 - discount_pct / 100.0)
                tot_amount = final_item_price * item["qty"]

                order = Order(
                    product_id=p.id,
                    user_id=u_id,
                    quantity=item["qty"],
                    gateway_order_id=f"order_demo_{1000 + i}",
                    gateway_payment_id=f"pay_demo_{2000 + i}",
                    provider="razorpay",
                    payment_status=item["status"],
                    total_amount=round(tot_amount, 2),
                    discount_applied=discount_pct,
                    created_at=now - timedelta(days=item["days_ago"], hours=i * 2),
                )
                session.add(order)

            await session.commit()
            logger.info("Successfully seeded realistic demo orders for merchant analytics.")
        except Exception as e:
            logger.warning("Could not auto-seed orders for analytics: %s", e)

    @classmethod
    async def get_dashboard_metrics(cls, time_range: str = "all") -> Dict[str, Any]:
        """
        Fetch aggregated business analytics, revenue, top-selling items,
        inventory status, and AI negotiation metrics.
        Supported time_range values: 'today', '7d', '30d', 'all'.
        """
        async with db_connection.get_session() as session:
            await cls._ensure_seed_orders_if_empty(session)

            # Query all valid orders with attached product and user
            statement = (
                select(Order)
                .options(joinedload(Order.product), joinedload(Order.user))
                .order_by(Order.created_at.desc())
            )
            results = await session.execute(statement)
            all_orders = results.scalars().all()

            # Filter by time range if requested
            now = datetime.now()
            cutoff_date = None
            if time_range == "today":
                cutoff_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_range == "7d":
                cutoff_date = now - timedelta(days=7)
            elif time_range == "30d":
                cutoff_date = now - timedelta(days=30)

            filtered_orders = []
            for ord_obj in all_orders:
                if cutoff_date and ord_obj.created_at and ord_obj.created_at < cutoff_date:
                    continue
                # Exclude failed or cancelled orders from revenue metrics
                st = (ord_obj.payment_status or "paid").lower()
                if st in ["failed", "cancelled", "refunded"]:
                    continue
                filtered_orders.append(ord_obj)

            total_revenue = 0.0
            total_cost = 0.0
            total_ai_discount_amount = 0.0
            total_original_revenue = 0.0
            total_items_sold = 0
            unique_customers = set()

            category_data = defaultdict(lambda: {"revenue": 0.0, "profit": 0.0, "count": 0, "cost": 0.0})
            trend_data = defaultdict(lambda: {"revenue": 0.0, "profit": 0.0, "discount_given": 0.0, "order_count": 0})
            product_sales = defaultdict(lambda: {
                "product": None,
                "units_sold": 0,
                "revenue": 0.0,
                "profit": 0.0,
                "orders_count": 0,
            })

            for order in filtered_orders:
                if not order.product:
                    continue

                prod = order.product
                qty = order.quantity or 1
                total_items_sold += qty

                if order.user_id:
                    unique_customers.add(order.user_id)

                orig_item_price = float(prod.price)
                cost_item_price = float(prod.cost_price or 0.0)
                disc_pct = float(order.discount_applied or 0.0)

                order_tot = float(order.total_amount or 0.0)
                if order_tot > 0:
                    final_price_per_unit = order_tot / qty
                else:
                    final_price_per_unit = orig_item_price * (1.0 - disc_pct / 100.0)

                final_order_revenue = final_price_per_unit * qty
                total_order_cost = cost_item_price * qty
                order_discount_rupees = max(0.0, (orig_item_price * qty) - final_order_revenue)
                order_profit = max(0.0, final_order_revenue - total_order_cost)

                # Global aggregates
                total_original_revenue += orig_item_price * qty
                total_revenue += final_order_revenue
                total_cost += total_order_cost
                total_ai_discount_amount += order_discount_rupees

                # Category breakdown
                cat = prod.type.value if hasattr(prod.type, "value") else str(prod.type)
                category_data[cat]["revenue"] += final_order_revenue
                category_data[cat]["profit"] += order_profit
                category_data[cat]["cost"] += total_order_cost
                category_data[cat]["count"] += qty

                # Product level sales ("which item is selling more")
                p_entry = product_sales[prod.id]
                p_entry["product"] = prod
                p_entry["units_sold"] += qty
                p_entry["revenue"] += final_order_revenue
                p_entry["profit"] += order_profit
                p_entry["orders_count"] += 1

                # Date trend
                if order.created_at:
                    date_str = order.created_at.strftime("%Y-%m-%d")
                    trend_data[date_str]["revenue"] += final_order_revenue
                    trend_data[date_str]["profit"] += order_profit
                    trend_data[date_str]["discount_given"] += order_discount_rupees
                    trend_data[date_str]["order_count"] += 1

            total_profit = max(0.0, total_revenue - total_cost)
            avg_profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0.0
            avg_order_value = (total_revenue / len(filtered_orders)) if filtered_orders else 0.0
            avg_discount_pct = (
                (total_ai_discount_amount / total_original_revenue * 100.0)
                if total_original_revenue > 0
                else 0.0
            )

            # Format top-selling products
            top_selling = []
            for pid, pdata in sorted(product_sales.items(), key=lambda x: (x[1]["units_sold"], x[1]["revenue"]), reverse=True):
                p = pdata["product"]
                stock_qty = p.stock if p.stock is not None else 0
                stock_status = "In Stock"
                if stock_qty <= 0:
                    stock_status = "Out of Stock"
                elif stock_qty <= 10:
                    stock_status = "Low Stock"

                top_selling.append({
                    "product_id": p.id,
                    "name": p.name,
                    "brand": p.brand or "Dukaan",
                    "category": p.type.value if hasattr(p.type, "value") else str(p.type),
                    "image_url": p.image_url,
                    "price": round(float(p.price), 2),
                    "cost_price": round(float(p.cost_price or 0.0), 2),
                    "units_sold": pdata["units_sold"],
                    "total_revenue": round(pdata["revenue"], 2),
                    "total_profit": round(pdata["profit"], 2),
                    "current_stock": stock_qty,
                    "stock_status": stock_status,
                })

            # Fetch catalog inventory alerts (low stock items)
            alerts_statement = select(Product).where(Product.stock <= 10).order_by(Product.stock.asc()).limit(10)
            alerts_res = await session.execute(alerts_statement)
            low_stock_products = alerts_res.scalars().all()
            inventory_alerts = [
                {
                    "product_id": p.id,
                    "name": p.name,
                    "brand": p.brand or "Dukaan",
                    "category": p.type.value if hasattr(p.type, "value") else str(p.type),
                    "current_stock": p.stock or 0,
                    "price": round(float(p.price), 2),
                    "image_url": p.image_url,
                    "status": "Out of Stock" if (p.stock or 0) <= 0 else "Low Stock",
                }
                for p in low_stock_products
            ]

            # Format category breakdown
            formatted_category = []
            for cat, data in category_data.items():
                cat_rev = data["revenue"]
                cat_prof = data["profit"]
                cat_margin = (cat_prof / cat_rev * 100) if cat_rev > 0 else 0.0
                share_pct = (cat_rev / total_revenue * 100) if total_revenue > 0 else 0.0
                formatted_category.append({
                    "name": cat,
                    "revenue": round(cat_rev, 2),
                    "profit": round(cat_prof, 2),
                    "sales": data["count"],
                    "share_percent": round(share_pct, 1),
                    "margin_percent": round(cat_margin, 1),
                })
            formatted_category.sort(key=lambda x: x["revenue"], reverse=True)

            # Sort trends by date
            formatted_trend = []
            for date_str in sorted(trend_data.keys()):
                data = trend_data[date_str]
                formatted_trend.append({
                    "date": date_str,
                    "revenue": round(data["revenue"], 2),
                    "profit": round(data["profit"], 2),
                    "discount_given": round(data["discount_given"], 2),
                    "orders": data["order_count"],
                })

            # Negotiation and AI chat funnel analytics from MongoDB
            negotiation_funnel = await cls._get_mongo_negotiation_funnel()

            return {
                "time_range": time_range,
                "metrics": {
                    "total_revenue": round(total_revenue, 2),
                    "total_profit": round(total_profit, 2),
                    "profit_margin_percent": round(avg_profit_margin, 1),
                    "total_orders": len(filtered_orders),
                    "total_items_sold": total_items_sold,
                    "average_order_value": round(avg_order_value, 2),
                    "total_ai_discount_amount": round(total_ai_discount_amount, 2),
                    "average_discount_percent": round(avg_discount_pct, 1),
                    "active_customers": len(unique_customers),
                },
                "top_selling_products": top_selling,
                "inventory_alerts": inventory_alerts,
                "revenue_by_category": formatted_category,
                "revenue_trend": formatted_trend,
                "negotiation_analytics": negotiation_funnel,
            }

    @staticmethod
    async def _get_mongo_negotiation_funnel() -> Dict[str, Any]:
        """Aggregates negotiation metrics directly from MongoDB dukaan_audit collections."""
        try:
            from Chat.database import chat_audit_repo
            threads = await chat_audit_repo.collection.find().limit(200).to_list(length=200)

            total_sessions = len(threads)
            negotiation_rounds = 0
            agreed_count = 0
            orders_placed_count = 0
            requested_sum = 0.0
            granted_sum = 0.0

            for t in threads:
                st = t.get("state") or {}
                if st.get("order_placed"):
                    orders_placed_count += 1

                logs = st.get("negotiation_log") or []
                if logs:
                    negotiation_rounds += len(logs)
                    for log in logs:
                        req_val = float(log.get("requested") or 0.0)
                        off_val = float(log.get("agent_offered") or 0.0)
                        requested_sum += req_val
                        granted_sum += off_val
                        if log.get("accepted"):
                            agreed_count += 1

            avg_req = (requested_sum / negotiation_rounds) if negotiation_rounds > 0 else 0.0
            avg_granted = (granted_sum / negotiation_rounds) if negotiation_rounds > 0 else 0.0
            conversion_rate = (orders_placed_count / total_sessions * 100) if total_sessions > 0 else 0.0

            return {
                "total_chat_sessions": total_sessions,
                "total_negotiation_rounds": negotiation_rounds,
                "agreed_deals_count": agreed_count,
                "average_discount_requested": round(avg_req, 1),
                "average_discount_granted": round(avg_granted, 1),
                "conversion_rate": round(conversion_rate, 1),
                "orders_placed_from_chat": orders_placed_count,
            }
        except Exception as e:
            logger.warning("Could not fetch negotiation funnel from Mongo: %s", e)
            return {
                "total_chat_sessions": 0,
                "total_negotiation_rounds": 0,
                "agreed_deals_count": 0,
                "average_discount_requested": 0.0,
                "average_discount_granted": 0.0,
                "conversion_rate": 0.0,
                "orders_placed_from_chat": 0,
            }


analytics_service = AnalyticsService()
