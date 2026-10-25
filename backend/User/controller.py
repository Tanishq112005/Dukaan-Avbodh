import logging
from typing import Optional
from fastapi import HTTPException, status
from User.database import userRepository, UserRepository

logger = logging.getLogger(__name__)


class UserController:
    def __init__(self, user_repo: Optional[UserRepository] = None):
        self.user_repo = user_repo or userRepository

    async def get_by_id(self, user_id: int):
        try:
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            return user
        except HTTPException:
            raise
        except Exception:
            logger.exception("Failed to get user by id %s", user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user"
            )

    async def update_profile(
        self,
        user_id: int,
        name: Optional[str] = None,
        email: Optional[str] = None,
        address: Optional[str] = None
    ):
        try:
            user = await self.user_repo.update_profile(
                user_id=user_id,
                name=name,
                email=email,
                address=address
            )
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            return user
        except HTTPException:
            raise
        except Exception:
            logger.exception("Failed to update profile for user %s", user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user profile"
            )


userController = UserController()
