from mcp_server.server import mcp
from repositories import ProductRepository
from models.product import ProductType

product_repo = ProductRepository()


@mcp.resource("catalog://product-types")
async def list_product_types() -> dict:
    """
    Returns a list of all available product categories in the merchant's catalog.
    
    LLM Instructions:
    - ALWAYS read this resource before calling get_products_by_type() to ensure you use a valid category name.
    """
    return {
        "available_types": [t.value for t in ProductType],
        "description": "Use these exact values when calling the get_products_by_type() tool."
    }


@mcp.tool()
async def get_catalog() -> dict:
    """
    Retrieves the complete catalog of currently available (in-stock) products.
    
    LLM Instructions:
    - Use this tool to browse the entire store inventory when the user wants to see everything.
    - All returned products are already confirmed to be in-stock.
    - DO NOT ask the user for product IDs; refer to products by their 'name' in conversation.
    """
    products = await product_repo.get_in_stock()
    
    # Exclude sensitive merchant data AND discount info so the LLM doesn't see or leak it
    return {
        "success": True,
        "products": [
            p.model_dump(exclude={"cost_price", "min_profit_margin_percent", "stock", "discount"}) 
            for p in products
        ]
    }


@mcp.tool()
async def get_products_by_type(product_type: str) -> dict:
    """
    Retrieves a list of in-stock products for a specific category (e.g., 't-shirt', 'jeans').
    
    LLM Instructions:
    - Use this tool when the user is looking for a specific type of clothing.
    - MUST pass a valid product_type. Read 'catalog://product-types' first if unsure.
    - All returned products are confirmed to be in-stock.
    """
    try:
        parsed_type = ProductType(product_type)
    except ValueError:
        return {
            "success": False,
            "error": f"'{product_type}' is not a valid category.",
            "valid_types": [t.value for t in ProductType]
        }

    products = await product_repo.get_by_type(parsed_type)
    
    # Exclude sensitive merchant data AND discount info
    return {
        "success": True, 
        "products": [
            p.model_dump(exclude={"cost_price", "min_profit_margin_percent", "stock", "discount"}) 
            for p in products
        ]
    }