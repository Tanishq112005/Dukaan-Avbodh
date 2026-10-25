from fastapi import APIRouter

from .schemas import SignupRequest, LoginRequest
from .controller import authController

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", status_code=200)
async def signup(payload: SignupRequest):
    return await authController.signup(payload)


@router.post("/login")
async def login(payload: LoginRequest):
    return await authController.login(payload)
