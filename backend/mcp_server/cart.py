from typing import Optional
from mcp_server.server import mcp
from repositories.cart_repository import cart_repository


@mcp.tool()
async def add_to_cart(user_id: int, product_id: int, quantity: int = 1, size: Optional[str] = None) -> dict:
    """
    Adds a product to the user's cart. If the same product and size already exist in the cart, 
    it increments the quantity instead of creating a new row. Returns the updated cart.

    LLM Instructions:
    - DO use the returned 'cart' array to summarize the updated cart contents to the user.
    - DO NOT expose raw database fields like 'added_item_id' or 'product_id' directly to the user.
    - Structure your response to gracefully confirm the addition, showing the item's name, size, and updated quantity in a user-friendly format.
    """
    try:
        item = await cart_repository.add_item(user_id, product_id, quantity, size)
        cart_items = await cart_repository.get_cart_items(user_id)
        return {"success": True, "added_item_id": item.id, "cart": cart_items}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def remove_from_cart(user_id: int, product_id: int, size: Optional[str] = None) -> dict:
    """
    Completely removes a specific product from the user's cart, regardless of its current quantity.

    LLM Instructions:
    - DO check the 'success' boolean to confirm removal before updating the user.
    - DO NOT show technical error strings directly to the user.
    - If successful, reassure the user that the item was removed and optionally mention the remaining items in the 'cart' array.
    """
    try:
        removed = await cart_repository.remove_item(user_id, product_id, size)
        cart_items = await cart_repository.get_cart_items(user_id)
        return {"success": removed, "cart": cart_items}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def update_cart_item_quantity(
    user_id: int, product_id: int, quantity: int, size: Optional[str] = None
) -> dict:
    """
    Updates the quantity of a specific product in the cart. 
    Passing a quantity of 0 or less will completely remove the item from the cart.

    LLM Instructions:
    - DO analyze the requested quantity. If the quantity drops to 0, explicitly inform the user that the item was removed from the cart.
    - Format the updated quantity clearly.
    - DO NOT ask the user for internal IDs; always resolve the product by name in conversation before passing the product_id to this tool.
    """
    try:
        await cart_repository.update_quantity(user_id, product_id, quantity, size)
        cart_items = await cart_repository.get_cart_items(user_id)
        return {"success": True, "cart": cart_items}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_cart(user_id: int) -> dict:
    """
    Retrieves the user's current cart, including enriched product details and the calculated subtotal.
    
    LLM Instructions:
    - ALWAYS call this tool BEFORE making product recommendations, negotiating prices, or proceeding to checkout.
    - DO present the cart details to the user using clean formatting (e.g., a markdown list or table) showing item names, sizes, quantities, and price.
    - DO highlight the 'subtotal' value clearly.
    - DO NOT expose internal properties like 'cart_item_id' in your final response to the user.
    """
    try:
        cart_items = await cart_repository.get_cart_items(user_id)
        subtotal = sum(item["price"] * item["quantity"] for item in cart_items)
        return {"success": True, "cart": cart_items, "subtotal": round(subtotal, 2)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def clear_cart(user_id: int) -> dict:
    """
    Empties the entire cart for the user. 

    LLM Instructions:
    - ONLY call this tool after an order is successfully confirmed or upon explicit, unambiguous request from the user to delete everything.
    - DO inform the user that their cart is now completely empty.
    - DO NOT attempt to list cart items after this tool returns a success.
    """
    try:
        cleared = await cart_repository.clear_cart(user_id)
        return {"success": cleared}
    except Exception as e:
        return {"success": False, "error": str(e)}