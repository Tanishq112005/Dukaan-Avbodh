import logging
from typing import List, Any, Optional, Dict

from fastapi import HTTPException, status

from Product.database import productRepository
from Product.models import ProductType
from Product.schemas import ProductUpdate

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
            logger.exception("Failed to fetch products by ids")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch products by ids"
            )
     
    async def get_by_id(self, product_id: int):
        try:
            product = await productRepository.get_by_id(
                product_id=product_id
            )

            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )

            return {
                "success": True,
                "product": product
            }

        except HTTPException:
            raise

        except Exception:
            logger.exception("Failed to fetch product by id")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch product"
            )

    async def add_product(self, product, **kwargs):
        try:
            from Product.models import Product as ProductModel
            if not isinstance(product, ProductModel):
                if hasattr(product, "model_dump"):
                    data = product.model_dump()
                elif isinstance(product, dict):
                    data = dict(product)
                else:
                    data = vars(product)
                valid_fields = set(ProductModel.model_fields.keys())
                filtered = {k: v for k, v in data.items() if k in valid_fields}
                product_instance = ProductModel(**filtered)
            else:
                product_instance = product

            created_product = await productRepository.addProduct(
                product=product_instance
            )

            return {
                "success": True,
                "product": created_product
            }

        except Exception as e:
            logger.exception("Failed to add product: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add product: {str(e)}"
            )

    async def update_product(
        self,
        product_id: int,
        payload: Any
    ):
        try:
            existing = await productRepository.get_by_id(
                product_id=product_id
            )

            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )

            if hasattr(payload, "model_dump"):
                update_data = payload.model_dump(
                    exclude_unset=True,
                    exclude={"product_id"}
                )
            elif isinstance(payload, dict):
                update_data = {k: v for k, v in payload.items() if k != "product_id" and v is not None}
            else:
                update_data = {k: v for k, v in vars(payload).items() if k != "product_id" and v is not None}

            if not update_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fields provided for update"
                )

            updated_product = await productRepository.updateProduct(
                product_id=product_id,
                update_data=update_data
            )

            return {
                "success": True,
                "product": updated_product
            }

        except HTTPException:
            raise

        except Exception as e:
            logger.exception("Failed to update product: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update product: {str(e)}"
            )

    async def delete_product(self, product_id: int):
        try:
            existing = await productRepository.get_by_id(
                product_id=product_id
            )

            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )

            await productRepository.deleteProduct(
                product_id=product_id
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
