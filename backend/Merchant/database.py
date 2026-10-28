import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional, List, Dict, Any

from sqlmodel import select, func
from sqlalchemy.orm import joinedload

from config.database import db_connection
from config.mogodbconfig import nosql_client
from Order.models import Order
from Product.models import Product
from User.models import User
from Merchant.models import MerchantDiscountPolicy, DiscountPolicy
from Merchant.utils import (
    resolve_time_range,
    calculate_profit_margin,
    get_stock_status,
    serialize_mongo_doc,
)

logger = logging.getLogger(__name__)


# ==============================================================================
# Dedicated MongoDB Storage for Merchant Chats
# ==============================================================================

class MerchantChatRepository:
    """
    Dedicated MongoDB repository for storing and auditing Merchant AI Assistant
    conversations, agent state snapshots, and tool executions.
    Stored in MongoDB collection 'merchant_chats'.
    """

    def __init__(self, collection=None):
        self.collection = (
            collection
            if collection is not None
            else nosql_client.get_collection("dukaan_audit", "merchant_chats")
        )

    async def get_or_create_thread(self, merchant_id: int, thread_id: str) -> Dict[str, Any]:
        """Fetches or creates a persistent merchant chat thread in MongoDB."""
        try:
            thread = await self.collection.find_one({"merchant_id": merchant_id, "thread_id": thread_id})
            if not thread:
                now = datetime.utcnow()
                doc = {
                    "merchant_id": merchant_id,
                    "thread_id": thread_id,
                    "messages": [],
                    "state": {},
                    "created_at": now,
                    "updated_at": now,
                }
                res = await self.collection.insert_one(doc)
                doc["_id"] = res.inserted_id
                return serialize_mongo_doc(doc)
            return serialize_mongo_doc(thread)
        except Exception as e:
            logger.warning("[MERCHANT CHAT MONGO] Could not get/create thread: %s", e)
            return {"merchant_id": merchant_id, "thread_id": thread_id, "messages": [], "state": {}}

    async def add_message(
        self,
        merchant_id: int,
        thread_id: str,
        role: str,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Appends a message (merchant or assistant) to the merchant chat thread."""
        try:
            msg = {
                "role": role,
                "content": content,
                "tool_calls": tool_calls or [],
                "timestamp": datetime.utcnow(),
            }
            await self.collection.update_one(
                {"merchant_id": merchant_id, "thread_id": thread_id},
                {
                    "$push": {"messages": msg},
                    "$set": {"updated_at": datetime.utcnow()},
                },
                upsert=True,
            )
        except Exception as e:
            logger.warning("[MERCHANT CHAT MONGO] Could not append message: %s", e)

    async def update_thread_state(
        self,
        merchant_id: int,
        thread_id: str,
        state_snapshot: Dict[str, Any],
    ) -> None:
        """Saves a verifiable snapshot of the agent state into the MongoDB thread."""
        try:
            clean_state = serialize_mongo_doc(state_snapshot)
            await self.collection.update_one(
                {"merchant_id": merchant_id, "thread_id": thread_id},
                {
                    "$set": {
                        "state": clean_state,
                        "updated_at": datetime.utcnow(),
                    }
                },
                upsert=True,
            )
        except Exception as e:
            logger.warning("[MERCHANT CHAT MONGO] Could not update thread state: %s", e)

    async def get_merchant_threads(
        self,
        merchant_id: Optional[int] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Retrieves merchant chat history and state audit records."""
        try:
            query = {"merchant_id": merchant_id} if merchant_id else {}
            cursor = self.collection.find(query).sort("updated_at", -1).limit(limit)
            threads = await cursor.to_list(length=limit)
            return [serialize_mongo_doc(t) for t in threads]
        except Exception as e:
            logger.warning("[MERCHANT CHAT MONGO] Could not fetch threads: %s", e)
            return []


merchantChatRepo = MerchantChatRepository()


# ==============================================================================
# Merchant Domain Repository
# ==============================================================================

class MerchantRepository:
    """
    Data access repository for all Dukaan Merchant domain operations:
    - Real-time sales, profit, and customer analytics
    - Inventory alerts and catalog health
    - Auditing and chat transcript retrieval
    - Pricing policy bounds and order fulfillment tracking
    """

    # --------------------------------------------------------------------------
    # Database Seed Helper
    # --------------------------------------------------------------------------
    @staticmethod
    async def _ensure_seed_orders_if_empty(session):
        """
        Seeds realistic sample orders if the orders table is empty,
        ensuring merchant analytics dashboards render actionable data.
        """
        try:
            order_check = await session.execute(select(Order).limit(1))
            if order_check.scalars().first():
                return

            prods_res = await session.execute(select(Product).limit(30))
            products = prods_res.scalars().all()
            if not products:
                return

            users_res = await session.execute(select(User).limit(5))
            users = users_res.scalars().all()
            default_user_id = users[0].id if users else 1

            now = datetime.now()
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
            logger.info("Successfully seeded demo orders for merchant repository.")
        except Exception as e:
            logger.warning("Could not auto-seed orders: %s", e)

    # --------------------------------------------------------------------------
    # 1. Analytics & Executive Metrics
    # --------------------------------------------------------------------------
    async def get_dashboard_analytics(self, time_range: str = "all") -> Dict[str, Any]:
        """
        Aggregates store metrics across orders, revenue, profit, categories,
        trends, inventory alerts, and AI negotiation outcomes.
        """
        async with db_connection.get_session() as session:
            await self._ensure_seed_orders_if_empty(session)

            statement = (
                select(Order)
                .options(joinedload(Order.product), joinedload(Order.user))
                .order_by(Order.created_at.desc())
            )
            results = await session.execute(statement)
            all_orders = results.scalars().all()

            cutoff_date = resolve_time_range(time_range)

            filtered_orders: List[Order] = []
            for ord_obj in all_orders:
                if cutoff_date and ord_obj.created_at and ord_obj.created_at < cutoff_date:
                    continue
                st = (ord_obj.payment_status or "paid").lower()
                if st in ("failed", "cancelled", "refunded"):
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

                total_original_revenue += orig_item_price * qty
                total_revenue += final_order_revenue
                total_cost += total_order_cost
                total_ai_discount_amount += order_discount_rupees

                cat = prod.type.value if hasattr(prod.type, "value") else str(prod.type)
                category_data[cat]["revenue"] += final_order_revenue
                category_data[cat]["profit"] += order_profit
                category_data[cat]["cost"] += total_order_cost
                category_data[cat]["count"] += qty

                p_entry = product_sales[prod.id]
                p_entry["product"] = prod
                p_entry["units_sold"] += qty
                p_entry["revenue"] += final_order_revenue
                p_entry["profit"] += order_profit
                p_entry["orders_count"] += 1

                if order.created_at:
                    date_str = order.created_at.strftime("%Y-%m-%d")
                    trend_data[date_str]["revenue"] += final_order_revenue
                    trend_data[date_str]["profit"] += order_profit
                    trend_data[date_str]["discount_given"] += order_discount_rupees
                    trend_data[date_str]["order_count"] += 1

            total_profit = max(0.0, total_revenue - total_cost)
            avg_profit_margin = calculate_profit_margin(total_revenue, total_cost)
            avg_order_value = round(total_revenue / len(filtered_orders), 2) if filtered_orders else 0.0
            avg_discount_pct = (
                round((total_ai_discount_amount / total_original_revenue * 100.0), 1)
                if total_original_revenue > 0
                else 0.0
            )

            # Format top selling products
            top_selling = []
            for pid, pdata in sorted(
                product_sales.items(),
                key=lambda x: (x[1]["units_sold"], x[1]["revenue"]),
                reverse=True
            ):
                p = pdata["product"]
                stock_qty = p.stock if p.stock is not None else 0
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
                    "stock_status": get_stock_status(stock_qty),
                })

            # Fetch inventory alerts (stock <= 10)
            alerts_statement = select(Product).where(Product.stock <= 10).order_by(Product.stock.asc()).limit(15)
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
                    "status": get_stock_status(p.stock),
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

            # Fetch negotiation funnel
            negotiation_funnel = await self._get_mongo_negotiation_funnel()

            return {
                "time_range": time_range,
                "metrics": {
                    "total_revenue": round(total_revenue, 2),
                    "total_profit": round(total_profit, 2),
                    "profit_margin_percent": avg_profit_margin,
                    "total_orders": len(filtered_orders),
                    "total_items_sold": total_items_sold,
                    "average_order_value": avg_order_value,
                    "total_ai_discount_amount": round(total_ai_discount_amount, 2),
                    "average_discount_percent": avg_discount_pct,
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
        """Aggregates negotiation metrics directly from MongoDB customer chat threads."""
        try:
            from Chat.database import chat_audit_repo
            threads = await chat_audit_repo.collection.find().limit(200).to_list(length=200)

            total_sessions = len(threads)
            negotiation_rounds = 0
            agreed_count = 0
            orders_placed_count = 0
            requested_sum = 0.0
            granted_sum = 0.0
            product_discounts: Dict[str, Dict[str, Any]] = {}

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

                # Aggregate per-product negotiation and agreed discount history
                neg_prods = st.get("negotiated_products") or {}
                if isinstance(neg_prods, dict):
                    for pid_key, p_info in neg_prods.items():
                        if isinstance(p_info, dict):
                            p_name = p_info.get("product_name") or f"Product #{pid_key}"
                            p_disc = float(p_info.get("discount_percentage", 0.0) or 0.0)
                            if pid_key not in product_discounts:
                                product_discounts[pid_key] = {
                                    "product_id": p_info.get("product_id") or pid_key,
                                    "product_name": p_name,
                                    "times_negotiated": 0,
                                    "total_discount_sum": 0.0,
                                    "max_discount_given": 0.0,
                                }
                            product_discounts[pid_key]["times_negotiated"] += 1
                            product_discounts[pid_key]["total_discount_sum"] += p_disc
                            product_discounts[pid_key]["max_discount_given"] = max(
                                product_discounts[pid_key]["max_discount_given"], p_disc
                            )

            avg_req = (requested_sum / negotiation_rounds) if negotiation_rounds > 0 else 0.0
            avg_granted = (granted_sum / negotiation_rounds) if negotiation_rounds > 0 else 0.0
            conversion_rate = (orders_placed_count / total_sessions * 100) if total_sessions > 0 else 0.0

            product_breakdown = []
            for p_val in product_discounts.values():
                times = p_val["times_negotiated"]
                product_breakdown.append({
                    "product_id": p_val["product_id"],
                    "product_name": p_val["product_name"],
                    "negotiation_count": times,
                    "average_discount_percent": round(p_val["total_discount_sum"] / times, 1) if times > 0 else 0.0,
                    "max_discount_percent": round(p_val["max_discount_given"], 1),
                })

            return {
                "total_chat_sessions": total_sessions,
                "total_negotiation_rounds": negotiation_rounds,
                "agreed_deals_count": agreed_count,
                "average_discount_requested": round(avg_req, 1),
                "average_discount_granted": round(avg_granted, 1),
                "conversion_rate": round(conversion_rate, 1),
                "orders_placed_from_chat": orders_placed_count,
                "product_discount_breakdown": product_breakdown,
            }
        except Exception as e:
            logger.warning("[MERCHANT REPO] Could not fetch negotiation funnel from Mongo: %s", e)
            return {
                "total_chat_sessions": 0,
                "total_negotiation_rounds": 0,
                "agreed_deals_count": 0,
                "average_discount_requested": 0.0,
                "average_discount_granted": 0.0,
                "conversion_rate": 0.0,
                "orders_placed_from_chat": 0,
                "product_discount_breakdown": [],
            }

    # --------------------------------------------------------------------------
    # 2. Orders Management
    # --------------------------------------------------------------------------
    async def get_all_orders(self, limit: int = 100, skip: int = 0, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetches orders grouped by payment/gateway id with product and customer details.
        """
        async with db_connection.get_session() as session:
            stmt = (
                select(Order)
                .options(joinedload(Order.product), joinedload(Order.user))
                .order_by(Order.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            if status:
                stmt = stmt.where(Order.payment_status == status)

            results = await session.execute(stmt)
            orders = results.scalars().all()

            grouped_orders = {}
            for order in orders:
                group_id = order.gateway_order_id or str(order.id)
                if group_id not in grouped_orders:
                    grouped_orders[group_id] = {
                        "id": group_id,
                        "order_id": order.id,
                        "status": order.payment_status or "placed",
                        "payment_status": order.payment_status or "placed",
                        "discount_applied": float(order.discount_applied or 0.0),
                        "razorpay_order_id": order.gateway_order_id,
                        "razorpay_payment_id": order.gateway_payment_id,
                        "total_amount": float(order.total_amount or 0.0),
                        "created_at": order.created_at.isoformat() if order.created_at else None,
                        "products": [],
                        "user": {
                            "id": order.user.id if order.user else None,
                            "name": order.user.name if order.user else "Customer",
                            "email": order.user.email if order.user else "customer@dukaan.local",
                            "address": order.user.address if order.user and order.user.address else "Bangalore, India",
                        },
                    }

                if order.product:
                    grouped_orders[group_id]["products"].append({
                        "id": order.product.id,
                        "name": order.product.name,
                        "image_url": order.product.image_url,
                        "price": float(order.product.price),
                        "cost_price": float(order.product.cost_price or 0.0),
                        "brand": order.product.brand or "Dukaan",
                        "quantity": order.quantity or 1,
                    })

            return list(grouped_orders.values())

    async def get_order_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Fetches single order details by its primary ID."""
        async with db_connection.get_session() as session:
            stmt = (
                select(Order)
                .options(joinedload(Order.product), joinedload(Order.user))
                .where(Order.id == order_id)
            )
            res = await session.execute(stmt)
            order = res.scalars().first()
            if not order:
                return None

            return {
                "id": order.gateway_order_id or str(order.id),
                "order_id": order.id,
                "status": order.payment_status,
                "payment_status": order.payment_status,
                "discount_applied": float(order.discount_applied or 0.0),
                "razorpay_order_id": order.gateway_order_id,
                "razorpay_payment_id": order.gateway_payment_id,
                "total_amount": float(order.total_amount or 0.0),
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "product": {
                    "id": order.product.id,
                    "name": order.product.name,
                    "price": float(order.product.price),
                    "cost_price": float(order.product.cost_price or 0.0),
                } if order.product else None,
                "user": {
                    "id": order.user.id,
                    "name": order.user.name,
                    "email": order.user.email,
                } if order.user else None,
            }

    async def update_order_payment_status(self, order_id: int, new_status: str) -> Optional[Order]:
        """Updates the payment status of an order."""
        async with db_connection.get_session() as session:
            stmt = select(Order).where(Order.id == order_id)
            res = await session.execute(stmt)
            order = res.scalars().first()
            if not order:
                return None

            order.payment_status = new_status
            session.add(order)
            await session.commit()
            await session.refresh(order)
            return order

    # --------------------------------------------------------------------------
    # 3. Inventory & Stock Alerts
    # --------------------------------------------------------------------------
    async def get_inventory_alerts(self, threshold: int = 10) -> List[Dict[str, Any]]:
        """Fetches catalog products with stock count below or equal to threshold."""
        async with db_connection.get_session() as session:
            stmt = (
                select(Product)
                .where(Product.stock <= threshold)
                .order_by(Product.stock.asc())
            )
            res = await session.execute(stmt)
            products = res.scalars().all()
            return [
                {
                    "product_id": p.id,
                    "name": p.name,
                    "brand": p.brand or "Dukaan",
                    "category": p.type.value if hasattr(p.type, "value") else str(p.type),
                    "current_stock": p.stock or 0,
                    "price": round(float(p.price), 2),
                    "cost_price": round(float(p.cost_price or 0.0), 2),
                    "image_url": p.image_url,
                    "status": get_stock_status(p.stock),
                }
                for p in products
            ]

    # --------------------------------------------------------------------------
    # 4. Audit Logs & Chat Threads (MongoDB)
    # --------------------------------------------------------------------------
    async def get_audit_logs(self, limit: int = 200) -> List[Dict[str, Any]]:
        """Retrieves system and transaction audit logs from MongoDB."""
        try:
            from services.audit_logger import audit_logger
            cursor = audit_logger.collection.find().sort("timestamp", -1).limit(limit)
            logs = await cursor.to_list(length=limit)
            return [serialize_mongo_doc(l) for l in logs]
        except Exception as e:
            logger.exception("[MERCHANT REPO] Failed to fetch audit logs: %s", e)
            return []

    async def get_chat_threads(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieves customer bargaining sessions from MongoDB dukaan_audit.chat_threads."""
        try:
            from Chat.database import chat_audit_repo
            cursor = chat_audit_repo.collection.find().sort("updated_at", -1).limit(limit)
            threads = await cursor.to_list(length=limit)
            return [serialize_mongo_doc(t) for t in threads]
        except Exception as e:
            logger.exception("[MERCHANT REPO] Failed to fetch chat threads: %s", e)
            return []

    # --------------------------------------------------------------------------
    # 5. Pricing & Negotiation Bounds Policy
    # --------------------------------------------------------------------------
    async def get_or_create_discount_policy(self, merchant_id: int = 1) -> MerchantDiscountPolicy:
        """Fetches or initializes the store dynamic pricing policy bounds."""
        async with db_connection.get_session() as session:
            stmt = select(MerchantDiscountPolicy).where(MerchantDiscountPolicy.merchant_id == merchant_id)
            policy = (await session.execute(stmt)).scalars().first()
            if not policy:
                policy = MerchantDiscountPolicy(
                    merchant_id=merchant_id,
                    max_discount_percentage=25.0,
                    min_margin_percentage=15.0,
                    auto_accept_threshold=10.0,
                )
                session.add(policy)
                await session.commit()
                await session.refresh(policy)
            return policy

    async def update_discount_policy(
        self,
        merchant_id: int = 1,
        max_discount_percentage: Optional[float] = None,
        min_margin_percentage: Optional[float] = None,
        auto_accept_threshold: Optional[float] = None,
    ) -> MerchantDiscountPolicy:
        """Updates merchant negotiated pricing parameters."""
        async with db_connection.get_session() as session:
            stmt = select(MerchantDiscountPolicy).where(MerchantDiscountPolicy.merchant_id == merchant_id)
            policy = (await session.execute(stmt)).scalars().first()
            if not policy:
                policy = MerchantDiscountPolicy(merchant_id=merchant_id)
                session.add(policy)

            if max_discount_percentage is not None:
                policy.max_discount_percentage = max_discount_percentage
            if min_margin_percentage is not None:
                policy.min_margin_percentage = min_margin_percentage
            if auto_accept_threshold is not None:
                policy.auto_accept_threshold = auto_accept_threshold

            policy.updated_at = datetime.now()
            session.add(policy)
            await session.commit()
            await session.refresh(policy)
            return policy


merchantRepository = MerchantRepository()
