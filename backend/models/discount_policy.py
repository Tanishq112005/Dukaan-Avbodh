from sqlmodel import SQLModel, Field
from typing import Optional

class DiscountPolicy(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id")
    
    # --- Agent Negotiation Rules ---
    base_discount_percent: float = 0.0     # Default discount jo sabko milta hai bina mange
    max_discount_percent: float            # Agent isse zyada kabhi nahi dega (Hard Cap)
    agent_step_percent: float = 2.0        # User ke maangne par agent har step me kitna % badhayega
    min_loyalty_score: float = 0.0         # Max discount dene ke liye user ka behavior score kitna hona chahiye
    
    min_qty_for_discount: int = 1