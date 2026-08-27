# routes/auth_routes.py
from fastapi import APIRouter
from controllers.auth_controller import AuthController
from schemas.auth_schemas import SignupRequest, LoginRequest

router = APIRouter(prefix="/auth", tags=["Auth"])
controller = AuthController()

router.add_api_route("/signup", controller.signup, methods=["POST"])
router.add_api_route("/login", controller.login, methods=["POST"])