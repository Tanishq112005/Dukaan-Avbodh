# routes/product_routes.py
from fastapi import APIRouter, Depends
from controllers.product_controller import ProductController
from schemas.product_schemas import AddProductRequest
from middleware.auth_middleware import auth_middleware
from middleware.role_middleware import require_role
from models.user import UserRole

router = APIRouter(prefix="/product", tags=["Product"])
controller = ProductController()


# Sirf merchant access kar sakta hai
async def add_product_route(
    payload: AddProductRequest,
    current_user: dict = Depends(require_role(UserRole.MERCHANT))
):
    return await controller.add_product(payload, merchant_id=current_user["user_id"])


# Public route — koi bhi access kar sakta hai, auth ki zaroorat nahi
async def get_catalog_route():
    return await controller.get_catalog()


# Sirf logged-in (koi bhi role) access kar sakta hai
async def get_by_type_route(
    product_type: str,
    current_user: dict = Depends(auth_middleware)   # sirf auth check, role check nahi
):
    return await controller.get_by_type(product_type)


router.add_api_route("/add", add_product_route, methods=["POST"])
router.add_api_route("/catalog", get_catalog_route, methods=["GET"])
router.add_api_route("/type/{product_type}", get_by_type_route, methods=["GET"])