"""
Database Migration & Reset Utility
Drops all PostgreSQL tables EXCEPT 'product' to apply latest schema updates,
recreates all tables fresh from SQLModel metadata, and optionally clears stale Redis agent cache.
"""
import sys
import os
import asyncio

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from config.database import db_connection


async def main():
    print("=" * 60)
    print("Dukaan Database Reset Utility")
    print("Preserving 'product' catalog table. Resetting all other tables...")
    print("=" * 60)

    result = await db_connection.reset_tables_except_product()

    print("\n[OK] Dropped old tables:")
    for t in result["dropped_tables"]:
        print(f"  - {t}")

    print("\n[OK] Recreated tables matching current SQLModel schemas:")
    for t in result["current_tables"]:
        print(f"  + {t}")

    print(f"\n[VERIFIED] 'product' table preserved! Total products in catalog: {result['preserved_product_count']}")

    # Flush stale Redis agent states
    try:
        from config.redis import redisClient
        r = redisClient.get_redis_client()
        agent_keys = list(r.scan_iter("agent_state:*"))
        checkpointer_keys = list(r.scan_iter("checkpoint:*")) + list(r.scan_iter("checkpoint_writes:*"))
        all_stale_keys = agent_keys + checkpointer_keys
        if all_stale_keys:
            r.delete(*all_stale_keys)
            print(f"[REDIS] Cleaned {len(all_stale_keys)} stale agent cache and checkpointer keys.")
        else:
            print("[REDIS] No stale agent cache keys found.")
    except Exception as redis_err:
        print(f"[REDIS] Could not clear Redis (ignoring): {redis_err}")

    print("\n" + "=" * 60)
    print("Database reset completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
