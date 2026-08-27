# middleware/role_middleware.py
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from auth.auth_handler import AuthHandler
from models.user import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Har protected route ke liye — token decode karke user info deta hai."""
    payload = AuthHandler.decode_token(token)
    if "user_id" not in payload or "role" not in payload:
        raise HTTPException(status_code=401, detail="Token corrupt hai")
    return payload   # {"user_id": ..., "role": ...}


def require_role(*allowed_roles: UserRole):
    """
    Ek 'dependency factory' — isse specific roles ke liye routes ko lock kar sakte ho.
    Example: require_role(UserRole.MERCHANT) — sirf merchant access kar payega.
    """
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role")
        if user_role not in [r.value for r in allowed_roles]:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied — yeh action sirf {[r.value for r in allowed_roles]} kar sakte hain"
            )
        return current_user
    return role_checker