# middleware/auth_middleware.py
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from auth.auth_handler import AuthHandler

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


class AuthMiddleware:
    """
    Base authentication middleware — sirf yeh check karta hai ki
    valid token hai ya nahi. Role-check yahan nahi hota (woh RoleMiddleware
    alag se karega, isi ke upar build hoga).
    """

    def __init__(self):
        pass

    async def __call__(self, token: str = Depends(oauth2_scheme)) -> dict:
        payload = AuthHandler.decode_token(token)

        if "user_id" not in payload or "role" not in payload:
            raise HTTPException(status_code=401, detail="Token corrupt ya invalid hai")

        return payload   # {"user_id": ..., "role": ..., "exp": ...}


# ek shared instance — routes isi ko import karke Depends() mein use karenge
auth_middleware = AuthMiddleware()