from fastapi import APIRouter, Depends, Query
from typing import Optional

from .schemas import SignupRequest, LoginRequest, UpdateProfileRequest
from .controller import authController
from middleware.auth_middleware import auth_middleware

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", status_code=201)
async def signup(payload: SignupRequest):
    return await authController.signup(payload)


@router.post("/login")
async def login(payload: LoginRequest):
    return await authController.login(payload)


@router.get("/me")
@router.get("/profile")
async def get_my_profile(current_user: dict = Depends(auth_middleware)):
    return await authController.get_profile(current_user["user_id"])


@router.put("/profile")
async def update_my_profile(
    payload: UpdateProfileRequest,
    current_user: dict = Depends(auth_middleware),
):
    return await authController.update_profile(current_user["user_id"], payload)


@router.get("/status")
async def check_status(user_id: Optional[int] = Query(None)):
    return await authController.check_status(user_id)
