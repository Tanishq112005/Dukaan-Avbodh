import logging
from typing import Optional, List, Dict, Any, Union
from fastapi import HTTPException, status
from config.database import db_connection
from schemas.product_schemas import AddProductRequest
from repositories.product import Product as ProductRepo
from repositories.user import userRepository
from repositories.userEvent import userEvent
from models import Product, UserEvent, ProductType
from models.userEvent import EventType
from services.audit_logger import audit_logger

logger = logging.getLogger(__name__)


class ProductController:
    def __init__(self, product_repo: Optional[ProductRepo] = None, db=db_connection):
        self.db = db
        self.product_repo = product_repo if product_repo is not None else ProductRepo(self.db)
        self.event_repo = userEvent
        self.user_repo = userRepository
        self.audit_logger = audit_logger

    # ---------------------------------------------------------
    # 1. Add Product
    # ---------------------------------------------------------
    async def add_product(
        self,
        payload: Union[AddProductRequest, Product, Dict[str, Any]],
        merchant_id: Optional[int] = None
    ) -> Product:
        """
        Creates and adds a new product to the database via repository addProduct.
        Also records an audit log entry if merchant_id is provided.
        """
        if isinstance(payload, Product):
            product = payload
        elif isinstance(payload, AddProductRequest):
            product = Product(
                name=payload.name,
                price=payload.price,
                stock=payload.stock,
                type=payload.type,
                brand=payload.brand,
                gender=payload.gender,
                description=payload.description,
                sizes=payload.sizes,
                rating=payload.rating,
                discount=payload.discount,
                image_url=payload.image_url
            )
        elif isinstance(payload, dict):
            product = Product(**payload)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid product payload format."
            )

        try:
            created = await self.product_repo.addProduct(product)
        except Exception as e:
            logger.error(f"Error adding product: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add product: {str(e)}"
            )

        # Audit logging via service
        if merchant_id:
            try:
                await self.audit_logger.log_action(
                    action="product_added",
                    reason=f"merchant {merchant_id} added product '{created.name}'",
                    result=f"product_id={created.id}"
                )
            except Exception as log_err:
                logger.warning(f"Failed to log audit for product addition: {log_err}")

        return created

    # ---------------------------------------------------------
    # 2. Update Product
    # ---------------------------------------------------------
    async def update_product(
        self,
        product_id: int,
        updates: Dict[str, Any],
        merchant_id: Optional[int] = None
    ) -> Product:
        """
        Updates product attributes in the database (e.g. stock, price, etc.) via repository updateProduct.
        Raises 404 if product not found.
        """
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Updates dictionary cannot be empty."
            )

        try:
            updated = await self.product_repo.updateProduct(product_id, updates)
        except Exception as e:
            logger.error(f"Error updating product {product_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update product: {str(e)}"
            )

        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found."
            )

        if merchant_id:
            try:
                await self.audit_logger.log_action(
                    action="product_updated",
                    reason=f"merchant {merchant_id} updated product {product_id}",
                    result=f"updated_fields={list(updates.keys())}"
                )
            except Exception as log_err:
                logger.warning(f"Failed to log audit for product update: {log_err}")

        return updated

    # ---------------------------------------------------------
    # 3. Delete Product
    # ---------------------------------------------------------
    async def delete_product(
        self,
        product_id: int,
        merchant_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Deletes a product from the database via repository deleteProduct.
        Raises 404 if product not found.
        """
        try:
            deleted = await self.product_repo.deleteProduct(product_id)
        except Exception as e:
            logger.error(f"Error deleting product {product_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete product: {str(e)}"
            )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found."
            )

        if merchant_id:
            try:
                await self.audit_logger.log_action(
                    action="product_deleted",
                    reason=f"merchant {merchant_id} deleted product {product_id}",
                    result=f"product_id={product_id}"
                )
            except Exception as log_err:
                logger.warning(f"Failed to log audit for product deletion: {log_err}")

        return {
            "success": True,
            "message": f"Product with ID {product_id} deleted successfully."
        }

    # ---------------------------------------------------------
    # 4. Get by Type
    # ---------------------------------------------------------
    async def get_by_type(
        self,
        product_type: Union[str, ProductType]
    ) -> List[Product]:
        """
        Retrieves products of a specific type that are currently in stock (stock > 0).
        """
        if isinstance(product_type, ProductType):
            enum_type = product_type
        else:
            try:
                enum_type = ProductType(product_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid product type '{product_type}'. Valid options: {[t.value for t in ProductType]}"
                )

        return await self.product_repo.get_by_type(enum_type)

    # ---------------------------------------------------------
    # 5. Get by IDs
    # ---------------------------------------------------------
    async def get_by_ids(
        self,
        product_ids: List[int]
    ) -> List[Product]:
        """
        Retrieves products by a list of product IDs.
        """
        if not product_ids:
            return []
        return await self.product_repo.get_by_ids(product_ids)

    # ---------------------------------------------------------
    # Existing Catalog & Product Detail Helpers
    # ---------------------------------------------------------
    async def get_catalog(self) -> List[Product]:
        """Retrieves all products currently in stock."""
        return await self.product_repo.get_in_stock()

    async def get_product_detail(
        self,
        product_id: int,
        user_id: Optional[int] = None
    ) -> Product:
        """
        Retrieves product details by ID and logs a 'VIEWED' user event if user_id is provided.
        Raises 404 if the product is not found.
        """
        products = await self.product_repo.get_by_ids([product_id])
        product = products[0] if products else None

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found."
            )

        # Track user view event (Fail-safe wrapper)
        if user_id and self.event_repo:
            try:
                await self.event_repo.addUserEvents(
                    user_id=user_id,
                    event_type=EventType.VIEWED,
                    product_id=product.id
                )
            except Exception as e:
                logger.warning(f"Failed to record view event for user {user_id} on product {product_id}: {e}")

        return product

    # Aliases for naming flexibility
    addProduct = add_product
    updateProduct = update_product
    deleteProduct = delete_product
    getByType = get_by_type
    getByIds = get_by_ids
    getProductDetail = get_product_detail
    getCatalog = get_catalog


productController = ProductController()
