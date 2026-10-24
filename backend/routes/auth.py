from fastapi import APIRouter
from controllers.auth import auth

router = APIRouter(prefix="/auth", tags=["Auth"])


router.add_api_route("/signup", auth.signup, methods=["POST"])
router.add_api_route("/login", auth.login, methods=["POST"])