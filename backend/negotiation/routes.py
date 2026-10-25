from fastapi import APIRouter
from negotiation.controller import negotiationController
from negotiation.schemas import (
    MaxDiscountRequest,
    MaxDiscountResponse,
    NextDiscountRequest,
    NextDiscountResponse,
)

router = APIRouter(prefix="/negotiation", tags=["Negotiation"])


@router.post("/max-discount", response_model=MaxDiscountResponse)
async def calculate_maximum_discount(req: MaxDiscountRequest):
    """
    Calculate the maximum discount percentage possible across the provided items (or user cart)
    without breaching the merchant's required minimum profit margin.
    """
    return await negotiationController.get_max_discount(req)


@router.post("/next-discount", response_model=NextDiscountResponse)
async def calculate_next_discount(req: NextDiscountRequest):
    """
    Calculate the next counter-offer discount percentage for a user negotiation round.
    Currently treats every customer as loyal (concession factor = 0.40).
    """
    return await negotiationController.get_next_discount(req)
