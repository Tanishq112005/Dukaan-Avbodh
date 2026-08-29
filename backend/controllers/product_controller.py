# controllers/product_controller.py
from fastapi import HTTPException
from schemas.product_schemas import AddProductRequest
from repositories import ProductRepository
from repositories.user_event_repository import UserEventRepository
from models import Product, UserEvent
from models.user_event import EventType
from services.audit_logger import audit_logger


class ProductController:
    def __init__(self):
        self.product_repo = ProductRepository()
        self.event_repo = UserEventRepository()      # add kiya
        self.audit_logger = audit_logger              # add kiya (audit_repo nahi, audit_logger — service pattern follow karo)

    async def add_product(self, payload: AddProductRequest, merchant_id: int):
        product = Product(
            name=payload.name, price=payload.price,
            stock=payload.stock, type=payload.type,
            gender=payload.gender
        )
        created = await self.product_repo.create(product)

        await self.audit_logger.log_action(     # audit_repo → audit_logger
            action="product_added",
            reason=f"merchant {merchant_id} added product '{payload.name}'",
            result=f"product_id={created.id}"
        )
        return created

    async def get_catalog(self):
        return await self.product_repo.get_in_stock()

    async def get_by_type(self, product_type: str):
        from models.product import ProductType
        return await self.product_repo.get_by_type(ProductType(product_type))

    async def get_product_detail(self, product_id: int, user_id: int | None = None):
        product = await self.product_repo.get_by_id(product_id)

        if user_id and product:
            try:                                    # fail-safe wrapper add kiya
                await self.event_repo.create(UserEvent(
                    user_id=user_id,
                    product_id=product.id,
                    event_type=EventType.VIEWED,
                    category=product.type.value
                ))
            except Exception as e:
                print(f"[WARN] Event tracking fail hui: {e}")

        return product