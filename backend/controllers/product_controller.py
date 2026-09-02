import logging
from typing import Optional, List
from fastapi import HTTPException, status

from schemas.product_schemas import AddProductRequest
from repositories import ProductRepository
from repositories.user_event_repository import UserEventRepository
from repositories.user_repository import UserRepository
from models import Product, UserEvent, ProductType
from models.user_event import EventType
from services.audit_logger import audit_logger
from services.pricing_service import pricing_service

logger = logging.getLogger(__name__)


class ProductController:
    def __init__(self):
        self.product_repo = ProductRepository()
        self.event_repo = UserEventRepository()
        self.user_repo = UserRepository()
        self.audit_logger = audit_logger

    async def add_product(self, payload: AddProductRequest, merchant_id: int) -> Product:
        """Creates a new product in the database and records an audit log entry."""
        product = Product(
            name=payload.name,
            price=payload.price,
            stock=payload.stock,
            type=payload.type,
            gender=payload.gender
        )
        created = await self.product_repo.create(product)

        # Audit logging via service
        await self.audit_logger.log_action(
            action="product_added",
            reason=f"merchant {merchant_id} added product '{payload.name}'",
            result=f"product_id={created.id}"
        )
        return created

    async def get_catalog(self) -> List[Product]:
        """Retrieves all products currently in stock."""
        return await self.product_repo.get_in_stock()

    async def get_by_type(self, product_type: str) -> List[Product]:
        """Retrieves products filtered by ProductType enum."""
        try:
            enum_type = ProductType(product_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid product type '{product_type}'. Valid options: {[t.value for t in ProductType]}"
            )
            
        return await self.product_repo.get_by_type(enum_type)

    async def get_product_detail(self, product_id: int, user_id: Optional[int] = None) -> Product:
        """
        Retrieves product details by ID and logs a 'VIEWED' user event if user_id is provided.
        Raises 404 if the product is not found.
        """
        product = await self.product_repo.get_by_id(product_id)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found."
            )

        # Track user view event (Fail-safe wrapper)
        if user_id:
            try:
                await self.event_repo.create(UserEvent(
                    user_id=user_id,
                    product_id=product.id,
                    event_type=EventType.VIEWED,
                    category=product.type.value if hasattr(product.type, "value") else str(product.type)
                ))
            except Exception as e:
                logger.warning(f"Failed to record view event for user {user_id} on product {product_id}: {e}")

        return product