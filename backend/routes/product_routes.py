# routes/product_routes.py
from fastapi import APIRouter, Depends
from controllers.product_controller import ProductController
from schemas.product_schemas import AddProductRequest
from middleware.role_middleware import require_role, get_current_user
from models.user import UserRole

router = APIRouter(prefix="/product", tags=["Product"])
controller = ProductController()


async def add_product_route(
    payload: AddProductRequest,
    current_user: dict = Depends(require_role(UserRole.MERCHANT))   # sirf merchant!
):
    return await controller.add_product(payload, merchant_id=current_user["user_id"])


async def get_catalog_route():
    return await controller.get_catalog()


async def get_by_type_route(product_type: str):
    return await controller.get_by_type(product_type)


router.add_api_route("/add", add_product_route, methods=["POST"])
router.add_api_route("/catalog", get_catalog_route, methods=["GET"])
router.add_api_route("/type/{product_type}", get_by_type_route, methods=["GET"])