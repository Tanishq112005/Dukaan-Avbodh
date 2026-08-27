# mcp/product.py
from mcp_server.server import mcp
from repositories import ProductRepository
from models.product import ProductType

product_repo = ProductRepository()


@mcp.resource("catalog://product-types")
async def list_product_types() -> dict:
    """Merchant ke paas available saari product categories batata hai.
    Agent isse pehle padhega, taaki galat/random type na bheje."""
    return {
        "available_types": [t.value for t in ProductType],
        "description": "Yeh types get_products_by_type() tool mein use karo"
    }


@mcp.tool()
async def get_catalog() -> list[dict]:
    """Merchant ka poora product catalog return karta hai."""
    products = await product_repo.get_in_stock()
    return [p.model_dump() for p in products]


@mcp.tool()
async def get_products_by_type(product_type: str) -> dict:
    """Ek specific category (jaise 'footwear') ke products return karta hai.
    Valid types dekhne ke liye pehle 'catalog://product-types' resource padho."""
    try:
        parsed_type = ProductType(product_type)
    except ValueError:
        return {
            "success": False,
            "error": f"'{product_type}' valid type nahi hai",
            "valid_types": [t.value for t in ProductType]
        }

    products = await product_repo.get_by_type(parsed_type)
    return {"success": True, "products": [p.model_dump() for p in products]}


@mcp.tool()
async def check_stock(product_id: int) -> dict:
    """Ek product ka stock/availability check karta hai."""
    product = await product_repo.get_by_id(product_id)
    if not product:
        return {"found": False}
    return {"found": True, "stock": product.stock, "price": product.price}