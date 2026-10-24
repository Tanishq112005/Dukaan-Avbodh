import logging
from typing import List

from fastapi import HTTPException, status

from repositories.product import productRepository
from models.product import ProductType
from schemas.product import ProductUpdate

logger = logging.getLogger(__name__)




class ProductController:

    async def get_all_products(self):
        try:
            products = await productRepository.get_all_products()

            return {
                "success": True,
                "count": len(products),
                "products": products
            }

        except Exception:
            logger.exception("Failed to fetch all products")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch products"
            )

    async def get_list_of_items_in_stock(self):
        try:
            products = await productRepository.get_list_of_items_in_stock()

            return {
                "success": True,
                "count": len(products),
                "products": products
            }

        except Exception:
            logger.exception("Failed to fetch in-stock products")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch in-stock products"
            )

    async def get_list_of_items_in_stock_by_types(
        self,
        product_types: List[ProductType]
    ):
        try:
            products = (
                await productRepository
                .get_list_of_items_in_stock_by_types(
                    product_types=product_types
                )
            )

            return {
                "success": True,
                "count": len(products),
                "products": products
            }

        except Exception:
            logger.exception("Failed to fetch products by types")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch products by types"
            )

    async def get_by_type(self, product_type: ProductType):
        try:
            products = await productRepository.get_by_type(
                product_type=product_type
            )

            return {
                "success": True,
                "count": len(products),
                "products": products
            }

        except Exception:
            logger.exception("Failed to fetch products by type")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch products by type"
            )

    async def get_by_ids(self, product_ids: List[int]):
        try:
            products = await productRepository.get_by_ids(
                product_ids=product_ids
            )

            return {
                "success": True,
                "count": len(products),
                "products": products
            }

        except Exception:
            logger.exception("Failed to fetch products by IDs")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch products by IDs"
            )

    async def add_product(self, product):
        try:
            created_product = await productRepository.addProduct(
                product=product
            )

            return {
                "success": True,
                "message": "Product added successfully",
                "product": created_product
            }

        except Exception:
            logger.exception("Failed to add product")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add product"
            )

    async def update_product(self, payload: ProductUpdate):
        updates = payload.model_dump(
            exclude_unset=True,
            exclude={"product_id"}
        )

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide at least one field to update"
            )

        try:
            updated_product = await productRepository.updateProduct(
                product_id=payload.product_id,
                updates=updates
            )

            if updated_product is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product {payload.product_id} not found"
                )

            return {
                "success": True,
                "message": "Product updated successfully",
                "updated_fields": list(updates.keys()),
                "product": updated_product
            }

        except HTTPException:
            raise

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        except Exception:
            logger.exception(
                "Failed to update product %s",
                payload.product_id
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update product"
            )

    async def delete_product(self, product_id: int):
        try:
            deleted = await productRepository.deleteProduct(
                product_id=product_id
            )

            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )

            return {
                "success": True,
                "message": "Product deleted successfully"
            }

        except HTTPException:
            raise

        except Exception:
            logger.exception("Failed to delete product")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete product"
            )


productController = ProductController()
