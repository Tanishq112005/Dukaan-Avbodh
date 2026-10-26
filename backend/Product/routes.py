from typing import List

from fastapi import APIRouter, Depends, Query, HTTPException, status

from Product.models import ProductType
from Product.schemas import ProductUpdate
from Product.controller import productController
from middleware.auth_middleware import auth_middleware
from middleware.merchant_middleware import merchant_required


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


@router.get("/item")
async def get_all_products(
   
):
    return await productController.get_all_products()


@router.get("/item/Stock")
async def get_list_of_items_in_stock(
   
):
    return await productController.get_list_of_items_in_stock()


@router.get("/type")
async def get_list_of_items_in_stock_by_types(
    product_types: List[ProductType] = Query(...),
    
):
    return await productController.get_list_of_items_in_stock_by_types(
        product_types=product_types
    )


@router.get("/type/{product_type}")
async def get_by_type(
    product_type: ProductType,
   
):
    return await productController.get_by_type(
        product_type=product_type
    )


@router.get("/ids")
async def get_by_ids(
    product_ids: List[int] = Query(...),
   
):
    if merchant_required.check(current_user=current_user):
        return await productController.get_by_ids(
            product_ids=product_ids
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only merchants can access products by IDs."
    )


@router.post("/add")
async def add_product(
    payload: ProductUpdate,
    current_user: dict = Depends(auth_middleware)
):
    if merchant_required.check(current_user=current_user):
        return await productController.add_product(
            product=payload
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only merchants can add products."
    )


@router.patch("/update/{product_id}")
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    current_user: dict = Depends(auth_middleware)
):
    if merchant_required.check(current_user=current_user):
        payload.product_id = product_id

        return await productController.update_product(
            payload=payload
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only merchants can update products."
    )


@router.delete("/delete/{product_id}")
async def delete_product(
    product_id: int,
    current_user: dict = Depends(auth_middleware)
):
    if merchant_required.check(current_user=current_user):
        return await productController.delete_product(
            product_id=product_id
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only merchants can delete products."
    )
