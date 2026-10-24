
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from lib.jwt import AuthHandler

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class AuthMiddleware:

    async def __call__(
        self,
        token: str = Depends(oauth2_scheme)
    ) -> dict:

        try:
            payload = AuthHandler.decode_token(token)

            if not payload:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid or expired token"
                )

            user_id = payload.get("user_id")
            role = payload.get("role")

            if user_id is None or role is None:
                raise HTTPException(
                    status_code=401,
                    detail="Token is corrupt or invalid"
                )

            return {
                "user_id": int(user_id),
                "role": role
            }

        except HTTPException:
            raise

        except Exception:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired access token",
                headers={"WWW-Authenticate": "Bearer"}
            )


auth_middleware = AuthMiddleware()
