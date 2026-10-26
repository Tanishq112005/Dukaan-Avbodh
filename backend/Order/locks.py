import asyncio
import logging
from typing import List, Optional
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class ProductLockManager:
    """
    Manages concurrency locks for product inventory operations.
    
    Guarantees:
    1. Deadlock-Freedom: All requested product IDs are strictly sorted in ascending order
       before acquisition to prevent circular lock dependency.
    2. Distributed Locking: Uses Redis distributed locks with a finite TTL (lease time)
       and thread_local=False so crashes never orphan locks and async thread executors
       release cleanly.
    3. Resilience: Gracefully falls back to local asyncio mutexes if Redis is unreachable.
    """

    def __init__(self, ttl_seconds: int = 15, acquire_timeout: float = 10.0):
        self.ttl_seconds = ttl_seconds
        self.acquire_timeout = acquire_timeout
        self._local_locks: dict[int, asyncio.Lock] = {}
        self._local_meta_lock = asyncio.Lock()

    async def _get_local_lock(self, product_id: int) -> asyncio.Lock:
        async with self._local_meta_lock:
            if product_id not in self._local_locks:
                self._local_locks[product_id] = asyncio.Lock()
            return self._local_locks[product_id]

    @asynccontextmanager
    async def acquire_locks(self, product_ids: List[int]):
        """
        Acquires locks for multiple products in sorted order.
        Yields control inside the critical section, then releases all locks in reverse order.
        """
        if not product_ids:
            yield
            return

        # 1. Deduplicate and sort IDs to strictly eliminate deadlocks
        sorted_ids = sorted(list(set(product_ids)))
        acquired_redis_locks = []
        acquired_local_locks = []

        # Try to obtain Redis client
        r_client = None
        try:
            from config.redis import redisClient
            r_client = redisClient.get_redis_client()
            r_client.ping()
        except Exception as conn_err:
            logger.debug("Redis unavailable for product locks, using local locks: %s", conn_err)
            r_client = None

        try:
            for pid in sorted_ids:
                if r_client:
                    # Redis lock with thread_local=False for async thread executor compatibility
                    lock_key = f"lock:product:{pid}"
                    redis_lock = r_client.lock(
                        lock_key,
                        timeout=self.ttl_seconds,
                        sleep=0.05,
                        blocking_timeout=self.acquire_timeout,
                        thread_local=False,
                    )
                    acquired = await asyncio.to_thread(redis_lock.acquire)
                    if not acquired:
                        raise TimeoutError(
                            f"Could not acquire lock for product {pid} within {self.acquire_timeout}s. "
                            "Another transaction is currently processing this product's inventory."
                        )
                    acquired_redis_locks.append(redis_lock)
                else:
                    # Local fallback lock
                    local_lock = await self._get_local_lock(pid)
                    try:
                        await asyncio.wait_for(local_lock.acquire(), timeout=self.acquire_timeout)
                        acquired_local_locks.append(local_lock)
                    except asyncio.TimeoutError:
                        raise TimeoutError(
                            f"Could not acquire local lock for product {pid} within {self.acquire_timeout}s."
                        )

            yield

        finally:
            # Release all acquired Redis locks (reverse order)
            for r_lock in reversed(acquired_redis_locks):
                try:
                    await asyncio.to_thread(r_lock.release)
                except Exception as rel_err:
                    logger.debug("Failed releasing Redis lock: %s", rel_err)

            # Release all acquired local locks
            for l_lock in reversed(acquired_local_locks):
                try:
                    l_lock.release()
                except RuntimeError:
                    pass


product_lock_manager = ProductLockManager()
