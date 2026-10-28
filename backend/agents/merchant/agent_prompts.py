"""
Backward-compatibility bridge for `agents.merchant.agent_prompts`.
Re-exports prompt functions from `agents.merchant.prompts`.
"""
from agents.merchant.prompts import (
    get_merchant_system_prompt,
    get_merchant_reminder,
    get_system_prompt,
    get_system_reminder,
)

__all__ = [
    "get_merchant_system_prompt",
    "get_merchant_reminder",
    "get_system_prompt",
    "get_system_reminder",
]
