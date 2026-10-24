from typing import Optional
from sqlmodel import select
from config.database import db_connection
from models import User
from models.user import UserRole
from models.cart import Cart as CartModel


class User:
    ### Initialization of the repo
    def __init__(self, db_connection):
        self.db = db_connection

    ### Create user and automatically create their cart
    async def create(self, user: User) -> User:
        async with self.db.get_session() as session:
            try:
                session.add(user)
                await session.commit()
                await session.refresh(user)

                # Each user has one cart: automatically create it when user is created
                existing_cart = (
                    await session.exec(
                        select(CartModel).where(CartModel.user_id == user.id)
                    )
                ).first()

                if not existing_cart:
                    cart = CartModel(user_id=user.id)
                    session.add(cart)
                    await session.commit()

                return user
            except Exception as e:
                await session.rollback()
                raise e

    ### Checking user is already there or not by email
    async def getUserByEmail(self, email: str) -> Optional[User]:
        async with self.db.get_session() as session:
            result = await session.exec(
                select(User).where(User.email == email)
            )
            return result.first()

    get_by_email = getUserByEmail
    get_by_identifier = getUserByEmail

    ### Get user by id
    async def get_by_id(self, user_id: int) -> Optional[User]:
        async with self.db.get_session() as session:
            return await session.get(User, user_id)

    ### Get or create user
    async def get_or_create(
        self,
        name: str,
        role: str,
        email: str,
        address: Optional[str] = None
    ) -> User:
        existing = await self.getUserByEmail(email)
        if existing:
            return existing
        new_user = User(
            name=name,
            role=role,
            email=email,
            address=address
        )
        return await self.create(new_user)

    ### Update user profile
    async def update_profile(
        self,
        user_id: int,
        name: Optional[str] = None,
        email: Optional[str] = None,
        address: Optional[str] = None,
    ) -> Optional[User]:
        async with self.db.get_session() as session:
            try:
                result = await session.exec(select(User).where(User.id == user_id))
                user = result.first()
                if not user:
                    return None
                if name:
                    user.name = name
                if email:
                    user.email = email
                if address:
                    user.address = address
                session.add(user)
                await session.commit()
                await session.refresh(user)
                return user
            except Exception as e:
                await session.rollback()
                raise e

    ### Update user address
    async def update_address(self, user_id: int, address: str) -> Optional[User]:
        async with self.db.get_session() as session:
            try:
                result = await session.exec(
                    select(User).where(User.id == user_id)
                )
                user = result.first()
                if user:
                    user.address = address
                    session.add(user)
                    await session.commit()
                    await session.refresh(user)
                return user
            except Exception as e:
                await session.rollback()
                raise e

    ### Ensure guest user exists (and their cart is created)
    async def ensure_guest_exists(self, user_id: int) -> Optional[User]:
        async with self.db.get_session() as session:
            try:
                result = await session.exec(select(User).where(User.id == user_id))
                user = result.first()
                if user:
                    # Ensure cart exists for existing user
                    existing_cart = (
                        await session.exec(
                            select(CartModel).where(CartModel.user_id == user.id)
                        )
                    ).first()
                    if not existing_cart:
                        session.add(CartModel(user_id=user.id))
                        await session.commit()
                    return user

                guest = User(
                    id=user_id,
                    name=f"Guest {user_id}",
                    role=UserRole.CUSTOMER,
                    email=f"guest_{user_id}@dukaan.local",
                )
                session.add(guest)
                await session.commit()
                await session.refresh(guest)

                # Automatically create the cart for the guest user
                cart = CartModel(user_id=guest.id)
                session.add(cart)
                await session.commit()

                return guest
            except Exception:
                await session.rollback()
                return None


userRepository = User(db_connection=db_connection)
