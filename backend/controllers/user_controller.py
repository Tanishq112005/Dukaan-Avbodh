from repositories import UserRepository


class UserController:
    def __init__(self):
        self.user_repo = UserRepository()

    async def get_profile(self, user_id: int):
        return await self.user_repo.get_by_id(user_id)