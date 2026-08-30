# mcp_server/cart.py
from typing import Optional
from mcp_server.server import mcp
from repositories.cart_repository import cart_repository


@mcp.tool()
async def add_to_cart(user_id: int, product_id: int, quantity: int = 1, size: Optional[str] = None) -> dict:
    """User ke cart mein ek product add karta hai. Agar wahi product+size already cart mein
    hai toh naya row banane ke bajaye quantity badha deta hai. Updated cart return karta hai."""
    try:
        item = await cart_repository.add_item(user_id, product_id, quantity, size)
        cart_items = await cart_repository.get_cart_items(user_id)
        return {"success": True, "added_item_id": item.id, "cart": cart_items}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def remove_from_cart(user_id: int, product_id: int, size: Optional[str] = None) -> dict:
    """User ke cart se ek product poori tarah hata deta hai (quantity chahe kuch bhi ho)."""
    removed = await cart_repository.remove_item(user_id, product_id, size)
    cart_items = await cart_repository.get_cart_items(user_id)
    return {"success": removed, "cart": cart_items}


@mcp.tool()
async def update_cart_item_quantity(
    user_id: int, product_id: int, quantity: int, size: Optional[str] = None
) -> dict:
    """Cart mein kisi product ki quantity update karta hai. quantity 0 ya kam bhejne par
    wo item cart se remove ho jaata hai."""
    await cart_repository.update_quantity(user_id, product_id, quantity, size)
    cart_items = await cart_repository.get_cart_items(user_id)
    return {"success": True, "cart": cart_items}


@mcp.tool()
async def get_cart(user_id: int) -> dict:
    """User ka current cart (product details + subtotal ke saath) return karta hai.
    Recommend ya negotiate karne se PEHLE agent ko yeh hamesha call karna chahiye."""
    cart_items = await cart_repository.get_cart_items(user_id)
    subtotal = sum(item["price"] * item["quantity"] for item in cart_items)
    return {"success": True, "cart": cart_items, "subtotal": round(subtotal, 2)}


@mcp.tool()
async def clear_cart(user_id: int) -> dict:
    """User ka pura cart khali kar deta hai — order confirm hone ke baad isko call karo."""
    cleared = await cart_repository.clear_cart(user_id)
    return {"success": cleared}
