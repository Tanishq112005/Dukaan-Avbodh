from fastapi import Depends, HTTPException, status
from User.models import UserRole
from middleware.auth_middleware import auth_middleware


class MerchantRoleChecker:
    async def check(self, current_user: dict) -> bool:
        user_role = current_user.get("role")

        if user_role != UserRole.MERCHANT.value:
            return False

        return True


merchant_required = MerchantRoleChecker()


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory to check if the authenticated user has one of the allowed roles.
    """
    async def role_checker(current_user: dict = Depends(auth_middleware)) -> dict:
        user_role = current_user.get("role")
        allowed_values = [r.value if hasattr(r, "value") else str(r) for r in allowed_roles]
        if user_role not in allowed_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied — required role: {allowed_values}"
            )
        return current_user
    return role_checker


get_current_user = auth_middleware
