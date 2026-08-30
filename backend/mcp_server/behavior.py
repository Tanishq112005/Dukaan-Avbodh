# mcp_server/behavior.py
#
# All tools that used to live here (get_user_affinity, get_recent_events,
# calculate_purchase_probability) have been folded directly into
# recommend_products and search_products (mcp_server/recommendation.py,
# mcp_server/search.py), which now fetch affinity/recent-events/purchase-
# probability internally and return them in a "why" block. No separate
# calls needed anymore. This file is intentionally empty — safe to delete
# manually along with its import in main.py.
