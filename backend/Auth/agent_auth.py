import os
import json
import time
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from jose import jwt
from config.redis import redisClient

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
ALGORITHM = "HS256"
DEFAULT_SESSION_TTL_SECONDS = 600  # 10 minutes
DEFAULT_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def create_agent_access_token(
    user_id: int,
    role: str = "customer",
    scopes: Optional[List[str]] = None,
) -> str:
    """Creates a signed JWT access token for the agent session matching Dukaan's JWT contract."""
    to_encode = {
        "user_id": user_id,
        "role": role,
        "scopes": scopes or ["profile:read", "cart:read", "cart:write", "order:read", "order:write"],
        "token_type": "agent_bearer",
    }
    expire = datetime.utcnow() + timedelta(minutes=DEFAULT_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


class AgentAuthService:
    """
    Manages external AI Agent authentication sessions using Redis.
    Enables zero-credential exposure: users authenticate and authorize agents
    directly on the Dukaan website without exposing passwords or sensitive tokens to LLMs.
    """

    def __init__(self, redis_instance=None):
        self.redis_instance = redis_instance or redisClient
        self._fallback_memory: Dict[str, Dict[str, Any]] = {}

    def _get_client(self):
        try:
            return self.redis_instance.get_redis_client()
        except Exception as e:
            logger.warning("[AGENT AUTH] Redis not accessible, falling back to memory: %s", e)
            return None

    def _session_key(self, session_id: str) -> str:
        return f"agent_auth:session:{session_id.strip()}"

    def _code_key(self, code: str) -> str:
        return f"agent_auth:code:{code.strip().upper()}"

    def get_frontend_base_url(self) -> str:
        """Resolves the frontend URL from environment with production/local fallbacks."""
        return os.getenv("FRONTEND_URL", "https://dukaan-avbodh.vercel.app").rstrip("/")

    def create_session(
        self,
        agent_name: str = "AI Shopping Assistant",
        scopes: Optional[List[str]] = None,
        custom_base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Creates a new pending agent authentication session and returns the authorization URL.
        """
        session_id = f"agtsess_{secrets.token_urlsafe(18)}"
        code = f"DUK-{secrets.randbelow(9000) + 1000}"
        scopes = scopes or ["profile:read", "cart:read", "cart:write", "order:read", "order:write"]

        now = time.time()
        session_data = {
            "session_id": session_id,
            "code": code,
            "agent_name": agent_name,
            "scopes": scopes,
            "status": "pending",
            "created_at": now,
            "expires_at": now + DEFAULT_SESSION_TTL_SECONDS,
            "user_id": None,
            "user_name": None,
            "user_email": None,
            "access_token": None,
        }

        client = self._get_client()
        if client:
            try:
                serialized = json.dumps(session_data)
                client.setex(self._session_key(session_id), DEFAULT_SESSION_TTL_SECONDS, serialized)
                client.setex(self._code_key(code), DEFAULT_SESSION_TTL_SECONDS, session_id)
            except Exception as e:
                logger.error("[AGENT AUTH] Redis write error, falling back to memory: %s", e)
                self._fallback_memory[session_id] = session_data
        else:
            self._fallback_memory[session_id] = session_data

        base_url = (custom_base_url or self.get_frontend_base_url()).rstrip("/")
        auth_url = f"{base_url}/auth/authorize?session_id={session_id}&code={code}&agent={agent_name}"

        return {
            "session_id": session_id,
            "code": code,
            "agent_name": agent_name,
            "scopes": scopes,
            "auth_url": auth_url,
            "expires_in": DEFAULT_SESSION_TTL_SECONDS,
            "status": "pending",
        }

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves session metadata by session_id."""
        client = self._get_client()
        if client:
            try:
                raw = client.get(self._session_key(session_id))
                if raw:
                    return json.loads(raw)
            except Exception as e:
                logger.error("[AGENT AUTH] Redis read error: %s", e)

        mem_session = self._fallback_memory.get(session_id)
        if mem_session and mem_session.get("expires_at", 0) > time.time():
            return mem_session
        return None

    def get_session_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Retrieves session metadata by 6-char user code."""
        client = self._get_client()
        if client:
            try:
                session_id = client.get(self._code_key(code))
                if session_id:
                    sid = session_id.decode("utf-8") if isinstance(session_id, bytes) else session_id
                    return self.get_session(sid)
            except Exception as e:
                logger.error("[AGENT AUTH] Redis read code error: %s", e)

        for s in self._fallback_memory.values():
            if s.get("code", "").upper() == code.strip().upper() and s.get("expires_at", 0) > time.time():
                return s
        return None

    def approve_session(
        self,
        session_id: str,
        user_id: int,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        user_role: str = "customer",
    ) -> Dict[str, Any]:
        """
        Marks an agent session as approved by the authenticated shopper.
        Mints a scoped JWT token for the agent.
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return {"success": False, "error": "Invalid or expired authorization session."}

        if session_data.get("status") == "approved":
            return {
                "success": True,
                "already_approved": True,
                "message": "Session already approved.",
                "user_id": session_data.get("user_id"),
            }

        access_token = create_agent_access_token(
            user_id=user_id,
            role=user_role,
            scopes=session_data.get("scopes"),
        )

        session_data["status"] = "approved"
        session_data["user_id"] = user_id
        session_data["user_name"] = user_name or "Shopper"
        session_data["user_email"] = user_email
        session_data["access_token"] = access_token
        session_data["approved_at"] = time.time()

        client = self._get_client()
        if client:
            try:
                serialized = json.dumps(session_data)
                # Keep active for another 10 minutes so agent can fetch
                client.setex(self._session_key(session_id), DEFAULT_SESSION_TTL_SECONDS, serialized)
            except Exception as e:
                logger.error("[AGENT AUTH] Redis approve error: %s", e)
                self._fallback_memory[session_id] = session_data
        else:
            self._fallback_memory[session_id] = session_data

        return {
            "success": True,
            "message": "Agent authorized successfully.",
            "session_id": session_id,
            "user_id": user_id,
            "agent_name": session_data.get("agent_name"),
        }

    def reject_session(self, session_id: str) -> Dict[str, Any]:
        """Marks an agent session as rejected."""
        session_data = self.get_session(session_id)
        if not session_data:
            return {"success": False, "error": "Invalid or expired authorization session."}

        session_data["status"] = "rejected"
        session_data["rejected_at"] = time.time()

        client = self._get_client()
        if client:
            try:
                serialized = json.dumps(session_data)
                client.setex(self._session_key(session_id), 300, serialized)
            except Exception as e:
                logger.error("[AGENT AUTH] Redis reject error: %s", e)
                self._fallback_memory[session_id] = session_data
        else:
            self._fallback_memory[session_id] = session_data

        return {
            "success": True,
            "message": "Agent authorization rejected.",
            "session_id": session_id,
        }


# Singleton instance
agentAuthService = AgentAuthService()
