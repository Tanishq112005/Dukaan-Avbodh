from fastapi import APIRouter, Depends
from middleware.auth_middleware import auth_middleware
from controllers.cart import cartController
from schemas.cart import (
    AddItemRequest,
    UpdateItemRequest,
    DeleteItemRequest,
    ApplyDiscountRequest
)

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.post("/add")
async def add_item(
    payload: AddItemRequest,
    current_user: dict = Depends(auth_middleware)
):
    return await cartController.add_item(
        user_id=current_user["user_id"],
        payload=payload
    )


@router.get("/items")
async def get_items(
    current_user: dict = Depends(auth_middleware)
):
    return await cartController.get_items(
        user_id=current_user["user_id"]
    )


@router.get("/summary")
async def get_summary(
    current_user: dict = Depends(auth_middleware)
):
    return await cartController.get_summary(
        user_id=current_user["user_id"]
    )


@router.put("/update")
async def update_item(
    payload: UpdateItemRequest,
    current_user: dict = Depends(auth_middleware)
):
    return await cartController.update_item(
        user_id=current_user["user_id"],
        payload=payload
    )


@router.delete("/remove")
async def delete_item(
    payload: DeleteItemRequest,
    current_user: dict = Depends(auth_middleware)
):
    return await cartController.delete_item(
        user_id=current_user["user_id"],
        payload=payload
    )


@router.patch("/discount")
async def apply_discount(
    payload: ApplyDiscountRequest,
    current_user: dict = Depends(auth_middleware)
):
    return await cartController.apply_discount(
        user_id=current_user["user_id"],
        payload=payload
    )


@router.delete("/clear")
async def clear_cart(
    current_user: dict = Depends(auth_middleware)
):
    return await cartController.clear_cart(
        user_id=current_user["user_id"]
    )
