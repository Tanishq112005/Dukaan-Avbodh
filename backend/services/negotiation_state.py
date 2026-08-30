# services/negotiation_state.py
#
# DEPRECATED — no longer used.
#
# Negotiation state is now kept by the CALLING AGENT (chat agent's own memory,
# or an external MCP agent's own memory), not on the server. The
# `negotiate_discount` MCP tool (mcp_server/pricing.py) is a pure function:
# the caller passes `current_discount_percent` in on every call and is
# responsible for remembering the returned `counter_offer_percent` for next
# time. This file is kept only so a stray import doesn't crash; safe to
# delete manually.
