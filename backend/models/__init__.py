# models/__init__.py
from .product import Product
from .order import Order
from .discount_policy import DiscountPolicy
from .user import User
from .user_event import UserEvent   # yeh line add karo

__all__ = ["Product", "Order", "DiscountPolicy", "User", "UserEvent"]   # yahan bhi add karo