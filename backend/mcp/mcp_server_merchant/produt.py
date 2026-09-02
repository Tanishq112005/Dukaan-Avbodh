from typing import Optional
from pydantic import BaseModel, Field
from fastapi import HTTPException
from mcp_server_merchant import mcp
from controllers.product_controller import ProductController
from schemas.product_schemas import AddProductRequest
from models.product import ProductType


# Initialize the controller
product_controller = ProductController()


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


# --- Input Schemas ---

class AddProductInput(BaseModel):
    merchant_id: int = Field(description="ID of the merchant adding the product")
    name: str = Field(description="Name of the product")
    price: float = Field(description="Price of the product")
    stock: int = Field(description="Initial stock quantity available")
    type: str = Field(description="Product category type (e.g., 't-shirt', 'jeans')")
    gender: Optional[str] = Field(default=None, description="Target gender for the product")


class GetProductsByTypeInput(BaseModel):
    product_type: str = Field(description="The category type of the product to filter by")


class GetProductDetailInput(BaseModel):
    product_id: int = Field(description="Unique ID of the product to retrieve")
    user_id: Optional[int] = Field(
        default=None, 
        description="Optional ID of the user viewing the product, used to record view analytics"
    )


# --- MCP Tools ---

@mcp.tool()
async def add_product(input_data: AddProductInput) -> dict:
    """Creates a new product in the catalog and records an audit log for the merchant."""
    try:
        # Map the MCP input schema to the internal FastAPI request schema
        payload = AddProductRequest(
            name=input_data.name,
            price=input_data.price,
            stock=input_data.stock,
            type=input_data.type,
            gender=input_data.gender
        )
        
        created_product = await product_controller.add_product(
            payload=payload, 
            merchant_id=input_data.merchant_id
        )
        
        return {
            "status": "success",
            "message": f"Product '{created_product.name}' added successfully.",
            "data": created_product.model_dump() if hasattr(created_product, "model_dump") else created_product
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to add product: {str(e)}"}


@mcp.tool()
async def get_catalog() -> dict:
    """Retrieves all active products currently in stock."""
    try:
        products = await product_controller.get_catalog()
        return {
            "status": "success",
            "count": len(products),
            "data": [p.model_dump() if hasattr(p, "model_dump") else p for p in products]
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to retrieve catalog: {str(e)}"}


@mcp.tool()
async def get_products_by_type(input_data: GetProductsByTypeInput) -> dict:
    """Retrieves a list of products filtered by a specific product type category."""
    try:
        products = await product_controller.get_by_type(product_type=input_data.product_type)
        return {
            "status": "success",
            "count": len(products),
            "data": [p.model_dump() if hasattr(p, "model_dump") else p for p in products]
        }
    except HTTPException as http_exc:
        return {"status": "error", "message": http_exc.detail}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}


@mcp.tool()
async def get_product_detail(input_data: GetProductDetailInput) -> dict:
    """Retrieves detailed information for a single product and optionally logs a user view event."""
    try:
        product = await product_controller.get_product_detail(
            product_id=input_data.product_id,
            user_id=input_data.user_id
        )
        return {
            "status": "success",
            "data": product.model_dump() if hasattr(product, "model_dump") else product
        }
    except HTTPException as http_exc:
        return {"status": "error", "message": http_exc.detail}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}