# mcp/user.py
from typing import Optional
from mcp_server.server import mcp
from repositories import UserRepository

user_repo = UserRepository()


### for checking real user details
def _is_real_email(identifier: Optional[str]) -> bool:
    if not identifier:
        return False
    ident = identifier.strip().lower()
    if ident.endswith("@dukaan.local") or ident.startswith("guest_"):
        return False
    return "@" in ident and "." in ident.split("@")[-1]


def _is_real_name(name: Optional[str]) -> bool:
    if not name or not name.strip():
        return False
    return not name.strip().lower().startswith("guest ")


def _is_real_address(address: Optional[str]) -> bool:
    return bool(address and address.strip())



def _profile_payload(user) -> dict:
    has_name = _is_real_name(user.name)
    has_email = _is_real_email(user.identifier)
    has_address = _is_real_address(user.address)
    missing = []
    if not has_name:
        missing.append("name")
    if not has_email:
        missing.append("email")
    if not has_address:
        missing.append("address")
    return {
        "success": True,
        "user_id": user.id,
        "name": user.name if has_name else None,
        "email": user.identifier if has_email else None,
        "address": user.address if has_address else None,
        "has_name": has_name,
        "has_email": has_email,
        "has_address": has_address,
        "is_complete": len(missing) == 0,
        "missing_fields": missing,
    }


@mcp.tool()
async def register_buyer(name: str, buyer_role: str, identifier: str) -> dict:
    """Ek naya buyer (customer ya agent) register karta hai, taaki baad mein order create kar sake."""
    user = await user_repo.get_or_create(name=name, role=buyer_role, identifier=identifier)
    return {"success": True, "user_id": user.id, "role": user.role}


@mcp.tool()
async def get_user_details(user_id: int) -> dict:
    """
    Fetch saved checkout details (name, email, address) for this shopper.

    LLM Instructions:
    - ALWAYS call this BEFORE asking for delivery details or calling create_order.
    - IF is_complete is true: read the details back to the user and ask them to CONFIRM
      the address, or say they want to change it. Do not re-collect fields you already have.
    - IF missing_fields is not empty: ask ONLY for those missing fields.
    """
    await user_repo.ensure_guest_exists(user_id)
    user = await user_repo.get_by_id(user_id)
    if not user:
        return {
            "success": True,
            "user_id": user_id,
            "name": None,
            "email": None,
            "address": None,
            "has_name": False,
            "has_email": False,
            "has_address": False,
            "is_complete": False,
            "missing_fields": ["name", "email", "address"],
        }
    return _profile_payload(user)


@mcp.tool()
async def update_user_details(
    user_id: int,
    name: Optional[str] = None,
    email: Optional[str] = None,
    address: Optional[str] = None,
) -> dict:
    """
    Save or replace the shopper's name, email, and/or delivery address.

    LLM Instructions:
    - Call this when the user provides missing details or asks to change an existing field.
    - Only pass the fields that should be updated.
    """
    await user_repo.ensure_guest_exists(user_id)
    user = await user_repo.update_profile(
        user_id=user_id,
        name=name,
        email=email,
        address=address,
    )
    if not user:
        return {"success": False, "error": "User not found."}
    return _profile_payload(user)
