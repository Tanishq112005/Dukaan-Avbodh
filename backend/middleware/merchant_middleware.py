from fastapi import Depends, HTTPException, status
from models.user import UserRole


class MerchantRoleChecker:
    async def check(self, current_user: dict ) -> dict:
        user_role = current_user.get("role")

        if user_role != UserRole.MERCHANT.value:
            return False

        return True


merchant_required = MerchantRoleChecker()