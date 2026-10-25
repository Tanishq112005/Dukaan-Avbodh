from typing import List
from models.product import Product


def maximumDiscountPossible(itemsList: List[Product]) -> float:
    """
    Calculate the maximum discount percentage possible across the items in the cart
    without breaching the merchant's required minimum profit margin.

    Formula:
      - minimum_selling_price_per_item = cost_price + (cost_price * min_profit_margin_percent / 100)
      - total_minimum_selling_price = sum(minimum_selling_price_per_item)
      - total_selling_price = sum(price)

    Discount is applied against the total selling price:
      discount_amount = total_selling_price * (discount_percentage / 100)
      final_price = total_selling_price - discount_amount

    To ensure final_price >= total_minimum_selling_price:
      discount_percentage <= ((total_selling_price - total_minimum_selling_price) / total_selling_price) * 100
    """
    if not itemsList:
        return 0.0

    total_minimum_selling_price = 0.0
    total_selling_price = 0.0

    for eachItem in itemsList:
        costPrice = float(eachItem.cost_price or 0.0)
        minimumProfitMargin = float(eachItem.min_profit_margin_percent or 0.0)
        sellingPrice = float(eachItem.price or 0.0)

        min_item_selling_price = costPrice + ((costPrice * minimumProfitMargin) / 100.0)
        total_minimum_selling_price += min_item_selling_price
        total_selling_price += sellingPrice

    # If selling price is 0 or less than minimum required selling price, no discount is possible
    if total_selling_price <= 0 or total_selling_price <= total_minimum_selling_price:
        return 0.0

    # Discount calculated off selling price so applying it never drops below total_minimum_selling_price
    maximum_discount_possible = (
        (total_selling_price - total_minimum_selling_price) / total_selling_price
    ) * 100.0

    return round(maximum_discount_possible, 2)
