# routes/checkout_routes.py
from fastapi import APIRouter, Depends
from controllers.checkout_controller import CheckoutController
from schemas.checkout_schemas import CheckoutRequest
from middleware.role_middleware import get_current_user, require_role
from models.user import UserRole
from middleware.auth_middleware import auth_middleware

router = APIRouter(prefix="/checkout", tags=["Checkout"])
controller = CheckoutController()


async def checkout_route(
    payload: CheckoutRequest,
    current_user: dict = Depends(require_role(UserRole.CUSTOMER, UserRole.AI_AGENT))   # merchant checkout nahi karega
):
    return await controller.checkout(payload, current_user["user_id"])


router.add_api_route("/", checkout_route, methods=["POST"])