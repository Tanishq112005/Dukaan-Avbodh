import os
import json
import logging
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status, Request

from Payment.factory import payment_gateway_factory
from Payment.schemas import (
    PaymentOrderCreateRequest,
    PaymentOrderResponse,
    PaymentVerifyRequest,
    PaymentVerifyResponse,
    PaymentStatusResponse,
)
from Order.database import order_repository, InsufficientStockError
from Order.models import PaymentStatus, Order as OrderModel

logger = logging.getLogger(__name__)


class PaymentController:
    """
    Controller coordinating payment gateways, concurrency-locked order placement,
    verification, status polling, and secure webhook handling.
    """

    def __init__(self, order_repo=None, gateway_factory=None):
        self.order_repo = order_repo or order_repository
        self.gateway_factory = gateway_factory or payment_gateway_factory

    async def create_payment_order(
        self,
        payload: PaymentOrderCreateRequest,
        user_id: Optional[int] = None,
    ) -> PaymentOrderResponse:
        """
        Creates a payment order with the selected payment gateway (e.g. Razorpay).
        """
        provider_name = payload.provider or "razorpay"
        gateway = self.gateway_factory.get_gateway(provider_name)

        receipt = payload.receipt or f"rcpt_{user_id or 'guest'}_{int(os.urandom(4).hex(), 16)}"
        notes = payload.notes or {}
        if user_id:
            notes["user_id"] = str(user_id)

        try:
            order_data = await gateway.create_order(
                amount=payload.amount,
                currency=payload.currency,
                receipt=receipt,
                notes=notes,
            )

            client_key = getattr(gateway, "client_key_id", None) or os.getenv("RAZORPAY_KEY_ID", "")

            # If order IDs are linked, update gateway_order_id in DB
            if payload.order_ids:
                from config.database import db_connection
                async with db_connection.get_session() as session:
                    from sqlmodel import select
                    res = await session.exec(
                        select(OrderModel).where(OrderModel.id.in_(payload.order_ids))
                    )
                    orders = res.all()
                    for o in orders:
                        o.gateway_order_id = order_data["id"]
                        o.provider = provider_name
                        session.add(o)
                    await session.commit()

            return PaymentOrderResponse(
                id=order_data["id"],
                amount=order_data["amount"],
                currency=order_data["currency"],
                status=order_data.get("status", "created"),
                receipt=order_data.get("receipt"),
                provider=provider_name,
                client_key_id=client_key,
            )

        except ValueError as val_err:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
        except Exception as e:
            logger.exception("Failed creating payment order: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment gateway order creation failed: {str(e)}",
            )

    async def verify_payment(
        self,
        payload: PaymentVerifyRequest,
        user_id: Optional[int] = None,
    ) -> PaymentVerifyResponse:
        """
        Cryptographically validates checkout signature and transitions orders to PAID.
        """
        provider_name = payload.provider or "razorpay"
        gateway = self.gateway_factory.get_gateway(provider_name)

        is_valid = gateway.verify_payment_signature(
            order_id=payload.razorpay_order_id,
            payment_id=payload.razorpay_payment_id,
            signature=payload.razorpay_signature,
        )

        if not is_valid:
            logger.warning(
                "Payment signature mismatch for razorpay_order_id=%s, payment_id=%s",
                payload.razorpay_order_id,
                payload.razorpay_payment_id,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment signature verification failed. Untrusted or forged payload.",
            )

        # Confirm orders in database
        updated_orders = await self.order_repo.confirm_order_payment(
            gateway_order_id=payload.razorpay_order_id,
            gateway_payment_id=payload.razorpay_payment_id,
            user_id=user_id,
        )

        # Clear cart for the purchasing user
        effective_uid = user_id
        if not effective_uid and updated_orders:
            effective_uid = updated_orders[0].user_id

        if effective_uid:
            try:
                from Cart.database import cart_repository
                await cart_repository.clear_cart(user_id=effective_uid)
            except Exception as cart_err:
                logger.warning("Could not auto-clear cart after payment: %s", cart_err)

        order_ids = [o.id for o in updated_orders] if updated_orders else payload.order_ids
        return PaymentVerifyResponse(
            success=True,
            message="Payment successfully verified and order confirmed.",
            order_ids=order_ids,
        )

    async def checkout_with_concurrency_lock(
        self,
        user_id: int,
        items: Optional[List[Dict[str, Any]]] = None,
        discount_percentage: float = 0.0,
        provider: str = "razorpay",
        currency: str = "INR",
        customer_name: Optional[str] = None,
        customer_email: Optional[str] = None,
        generate_payment_link: bool = False,
    ) -> Dict[str, Any]:
        """
        Full unified checkout workflow:
        1. Atomically locks inventory across requested products (preventing concurrent overselling).
        2. Deducts/reserves stock and creates pending order records.
        3. Generates a gateway order (Razorpay) and optional payment link.
        4. Associates gateway IDs with order rows.
        """
        gateway = self.gateway_factory.get_gateway(provider)

        # 1. Create order rows under strict concurrency lock & stock reservation
        try:
            orders = await self.order_repo.create_order_with_lock(
                user_id=user_id,
                items=items,
                discount_percentage=discount_percentage,
                provider=provider,
            )
        except InsufficientStockError as stock_err:
            logger.warning("Checkout blocked by stock check for user %s: %s", user_id, stock_err)
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(stock_err))
        except ValueError as val_err:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))

        order_ids = [o.id for o in orders]
        total_amount = sum(o.total_amount for o in orders)
        amount_paise = max(100, int(round(total_amount * 100)))

        # 2. Generate Razorpay payment order
        gateway_order_id = None
        payment_link_url = None
        payment_link_id = None

        try:
            rzp_order = await gateway.create_order(
                amount=amount_paise,
                currency=currency,
                receipt=f"rcpt_ord_{user_id}_{order_ids[0]}",
                notes={
                    "user_id": str(user_id),
                    "order_ids": ",".join(map(str, order_ids)),
                    "discount_applied": str(discount_percentage),
                },
            )
            gateway_order_id = rzp_order.get("id")

            if generate_payment_link:
                frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
                pl_res = await gateway.create_payment_link(
                    amount=amount_paise,
                    currency=currency,
                    description=f"Dukaan Order Checkout (#{order_ids[0]})",
                    customer={
                        "name": customer_name or f"Customer {user_id}",
                        "email": customer_email or f"user_{user_id}@dukaan.store",
                    },
                    callback_url=f"{frontend_url.rstrip('/')}/order-confirmed",
                    notes={
                        "order_id": gateway_order_id,
                        "user_id": str(user_id),
                    },
                )
                payment_link_url = pl_res.get("short_url")
                payment_link_id = pl_res.get("id")

        except Exception as pay_init_err:
            logger.error(
                "Payment gateway order creation failed after stock reservation. Cancelling orders: %s",
                pay_init_err,
            )
            # Rollback inventory reservation if gateway failed
            for oid in order_ids:
                try:
                    await self.order_repo.cancel_order_with_lock(oid, reason="gateway_init_failure")
                except Exception:
                    pass
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Payment gateway temporarily unavailable: {str(pay_init_err)}",
            )

        # 3. Update orders in DB with gateway identifiers
        from config.database import db_connection
        async with db_connection.get_session() as session:
            from sqlmodel import select
            res = await session.exec(select(OrderModel).where(OrderModel.id.in_(order_ids)))
            db_orders = res.all()
            for o in db_orders:
                o.gateway_order_id = gateway_order_id
                o.gateway_link_id = payment_link_id
                o.payment_link_url = payment_link_url
                session.add(o)
            await session.commit()

        client_key = getattr(gateway, "client_key_id", None) or os.getenv("RAZORPAY_KEY_ID", "")

        return {
            "success": True,
            "order_ids": order_ids,
            "total_amount": total_amount,
            "amount_paise": amount_paise,
            "currency": currency,
            "gateway_order_id": gateway_order_id,
            "payment_link_url": payment_link_url,
            "payment_link_id": payment_link_id,
            "provider": provider,
            "client_key_id": client_key,
            "message": "Order placed and stock reserved. Please proceed with payment.",
        }

    async def get_user_payment_status(self, user_id: int) -> PaymentStatusResponse:
        """
        Polls payment status for a user's most recent pending payment.
        Validates directly against Razorpay API when payment links are used.
        """
        from config.database import db_connection
        from sqlmodel import select

        async with db_connection.get_session() as session:
            res = await session.exec(
                select(OrderModel)
                .where(OrderModel.user_id == user_id)
                .order_by(OrderModel.created_at.desc())
            )
            latest_order = res.first()

        if not latest_order:
            return PaymentStatusResponse(
                success=True,
                paid=False,
                status="none",
                message="No recent orders found for user.",
            )

        if latest_order.payment_status in [PaymentStatus.PAID, PaymentStatus.COMPLETED]:
            return PaymentStatusResponse(
                success=True,
                paid=True,
                status="paid",
                message="Payment is complete.",
                payment_link=latest_order.payment_link_url,
                payment_link_id=latest_order.gateway_link_id,
                gateway_payment_id=latest_order.gateway_payment_id,
            )

        # If payment link ID exists, check real-time status with gateway
        gateway = self.gateway_factory.get_gateway(latest_order.provider or "razorpay")
        link_status = None
        gateway_payment_id = None

        if latest_order.gateway_link_id:
            try:
                link_data = await gateway.fetch_payment_link_status(latest_order.gateway_link_id)
                link_status = link_data.get("status")
                payments = link_data.get("payments") or []
                if payments:
                    gateway_payment_id = payments[0].get("payment_id") or payments[0].get("id")
            except Exception as e:
                logger.debug("Failed fetching payment link status from gateway: %s", e)

        paid = link_status == "paid"
        if paid:
            await self.order_repo.confirm_order_payment(
                gateway_order_id=latest_order.gateway_order_id,
                gateway_payment_id=gateway_payment_id,
                user_id=user_id,
            )
            # Clear user cart
            try:
                from Cart.database import cart_repository
                await cart_repository.clear_cart(user_id=user_id)
            except Exception:
                pass

        return PaymentStatusResponse(
            success=True,
            paid=paid,
            status=link_status or latest_order.payment_status,
            message="Payment is complete." if paid else "Payment is pending. Please complete transaction.",
            payment_link=latest_order.payment_link_url,
            payment_link_id=latest_order.gateway_link_id,
            gateway_payment_id=gateway_payment_id or latest_order.gateway_payment_id,
        )

    async def handle_webhook(self, request: Request) -> Dict[str, Any]:
        """
        Validates webhook cryptographic signature from Razorpay and processes
        'payment.captured', 'order.paid', or 'payment_link.paid' events.
        """
        try:
            body_bytes = await request.body()
            body = json.loads(body_bytes.decode("utf-8"))
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON body")

        signature = request.headers.get("X-Razorpay-Signature", "")
        gateway = self.gateway_factory.get_gateway("razorpay")

        # Validate signature if webhook secret is configured
        webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")
        if webhook_secret:
            is_valid = gateway.verify_webhook_signature(body_bytes, signature, webhook_secret)
            if not is_valid:
                logger.warning("Rejected webhook due to invalid signature.")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid webhook signature",
                )

        event = body.get("event", "")
        payload = body.get("payload") or {}
        payment_entity = (payload.get("payment") or {}).get("entity") or {}
        link_entity = (payload.get("payment_link") or {}).get("entity") or {}
        order_entity = (payload.get("order") or {}).get("entity") or {}

        is_paid = event in ("payment_link.paid", "payment.captured", "order.paid")
        if not is_paid:
            stat = link_entity.get("status") or payment_entity.get("status")
            is_paid = stat == "paid"

        if is_paid:
            notes = link_entity.get("notes") or order_entity.get("notes") or payment_entity.get("notes") or {}
            user_id = None
            try:
                user_id = int(notes.get("user_id")) if notes.get("user_id") else None
            except (TypeError, ValueError):
                user_id = None

            gateway_order_id = (
                order_entity.get("id")
                or payment_entity.get("order_id")
                or notes.get("order_id")
            )
            gateway_payment_id = payment_entity.get("id")

            updated = await self.order_repo.confirm_order_payment(
                gateway_order_id=gateway_order_id,
                gateway_payment_id=gateway_payment_id,
                user_id=user_id,
            )

            # Auto-clear cart for the user
            if user_id:
                try:
                    from Cart.database import cart_repository
                    await cart_repository.clear_cart(user_id=user_id)
                except Exception:
                    pass

            logger.info("Webhook successfully processed %s: updated %d orders", event, len(updated))
            return {"success": True, "event": event, "updated_orders_count": len(updated)}

        return {"success": True, "event": event, "ignored": True}


paymentController = PaymentController()
