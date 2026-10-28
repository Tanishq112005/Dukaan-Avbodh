import os
import sys
import time
import platform
import asyncio
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Server process start time
SERVER_START_TIME = time.time()


class HealthService:
    """
    Centralized health monitoring service for the Dukaan server.
    Provides diagnostic checks for PostgreSQL, Redis, MongoDB, RabbitMQ,
    AI subsystems, and host operating metrics with strict timeouts and error isolation.
    """

    def __init__(self):
        self.start_time = SERVER_START_TIME

    @property
    def uptime_seconds(self) -> float:
        return time.time() - self.start_time

    def format_uptime(self) -> str:
        seconds = int(self.uptime_seconds)
        days, rem = divmod(seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, secs = divmod(rem, 60)

        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0 or days > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or hours > 0 or days > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
        return " ".join(parts)

    def get_system_metrics(self) -> Dict[str, Any]:
        """Collects lightweight host and process metrics safely without external dependencies."""
        mem_rss_mb = None
        try:
            if sys.platform == "win32":
                import ctypes
                from ctypes import wintypes

                class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                    _fields_ = [
                        ("cb", wintypes.DWORD),
                        ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t),
                    ]

                counters = PROCESS_MEMORY_COUNTERS()
                counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
                handle = ctypes.windll.kernel32.GetCurrentProcess()
                if ctypes.windll.psapi.GetProcessMemoryInfo(
                    handle, ctypes.byref(counters), counters.cb
                ):
                    mem_rss_mb = round(counters.WorkingSetSize / (1024 * 1024), 2)
            else:
                import resource

                usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                # On macOS ru_maxrss is in bytes; on Linux in KB
                factor = 1024 * 1024 if sys.platform == "darwin" else 1024
                mem_rss_mb = round(usage / factor, 2)
        except Exception as e:
            logger.debug("Memory metric resolution skipped: %s", e)

        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "pid": os.getpid(),
            "threads_count": threading.active_count(),
            "memory_rss_mb": mem_rss_mb,
            "uptime_seconds": round(self.uptime_seconds, 2),
            "uptime_human": self.format_uptime(),
            "started_at": datetime.fromtimestamp(
                self.start_time, tz=timezone.utc
            ).isoformat(),
        }

    async def check_postgres(self, timeout: float = 3.0) -> Dict[str, Any]:
        """Checks PostgreSQL connectivity and measures query latency."""
        from config.database import db_connection
        from sqlalchemy import text

        start_t = time.perf_counter()
        try:
            async def _ping():
                async with db_connection.get_session() as session:
                    result = await session.execute(text("SELECT 1"))
                    return result.scalar()

            val = await asyncio.wait_for(_ping(), timeout=timeout)
            latency = (time.perf_counter() - start_t) * 1000
            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "message": "Connection active, query returned 1",
            }
        except asyncio.TimeoutError:
            latency = (time.perf_counter() - start_t) * 1000
            return {
                "status": "unhealthy",
                "latency_ms": round(latency, 2),
                "error": f"Connection timed out after {timeout}s",
            }
        except Exception as e:
            latency = (time.perf_counter() - start_t) * 1000
            return {
                "status": "unhealthy",
                "latency_ms": round(latency, 2),
                "error": str(e),
            }

    async def check_redis(self, timeout: float = 2.0) -> Dict[str, Any]:
        """Checks Redis connectivity and measures roundtrip ping latency."""
        from config.redis import redisClient

        start_t = time.perf_counter()
        try:
            client = redisClient.get_redis_client()

            def _sync_ping():
                return client.ping()

            # Execute sync redis call in thread pool to avoid blocking async event loop
            pong = await asyncio.wait_for(
                asyncio.to_thread(_sync_ping),
                timeout=timeout,
            )
            latency = (time.perf_counter() - start_t) * 1000
            return {
                "status": "healthy" if pong else "degraded",
                "latency_ms": round(latency, 2),
                "message": "PONG received successfully",
            }
        except asyncio.TimeoutError:
            latency = (time.perf_counter() - start_t) * 1000
            return {
                "status": "unhealthy",
                "latency_ms": round(latency, 2),
                "error": f"Ping timed out after {timeout}s",
            }
        except Exception as e:
            latency = (time.perf_counter() - start_t) * 1000
            return {
                "status": "unhealthy",
                "latency_ms": round(latency, 2),
                "error": str(e),
            }

    async def check_mongodb(self, timeout: float = 3.0) -> Dict[str, Any]:
        """Checks MongoDB connectivity via admin ping command."""
        from config.mogodbconfig import nosql_client

        start_t = time.perf_counter()
        try:
            client = nosql_client.get_client()

            async def _ping_mongo():
                return await client.admin.command("ping")

            res = await asyncio.wait_for(_ping_mongo(), timeout=timeout)
            latency = (time.perf_counter() - start_t) * 1000
            return {
                "status": "healthy" if res.get("ok") == 1.0 else "degraded",
                "latency_ms": round(latency, 2),
                "message": "MongoDB ping OK",
            }
        except asyncio.TimeoutError:
            latency = (time.perf_counter() - start_t) * 1000
            return {
                "status": "unhealthy",
                "latency_ms": round(latency, 2),
                "error": f"Ping timed out after {timeout}s",
            }
        except Exception as e:
            latency = (time.perf_counter() - start_t) * 1000
            return {
                "status": "unhealthy",
                "latency_ms": round(latency, 2),
                "error": str(e),
            }

    async def check_rabbitmq(self, timeout: float = 3.0) -> Dict[str, Any]:
        """Checks RabbitMQ message broker connectivity."""
        start_t = time.perf_counter()
        try:
            from rabbitmq.connection import RabbitMQConnection

            conn_mgr = RabbitMQConnection()

            async def _check_rabbit():
                conn = await conn_mgr.get_async_connection()
                return conn is not None and not conn.is_closed

            is_connected = await asyncio.wait_for(_check_rabbit(), timeout=timeout)
            latency = (time.perf_counter() - start_t) * 1000

            if is_connected:
                return {
                    "status": "healthy",
                    "latency_ms": round(latency, 2),
                    "message": "RabbitMQ AMQP connection established",
                }
            else:
                return {
                    "status": "degraded",
                    "latency_ms": round(latency, 2),
                    "message": "RabbitMQ broker not reachable or offline",
                }
        except asyncio.TimeoutError:
            latency = (time.perf_counter() - start_t) * 1000
            return {
                "status": "degraded",
                "latency_ms": round(latency, 2),
                "error": f"RabbitMQ connection timed out after {timeout}s",
            }
        except Exception as e:
            latency = (time.perf_counter() - start_t) * 1000
            return {
                "status": "degraded",
                "latency_ms": round(latency, 2),
                "error": str(e),
            }

    def check_agents(self) -> Dict[str, Any]:
        """Verifies state of user and merchant agent graphs."""
        from agents.user import agent_service
        from agents.merchant import agent_service as merchant_agent_service

        user_agent_ready = getattr(agent_service, "graph", None) is not None
        merchant_agent_ready = getattr(merchant_agent_service, "graph", None) is not None

        return {
            "user_agent": {
                "status": "ready" if user_agent_ready else "uninitialized",
            },
            "merchant_agent": {
                "status": "ready" if merchant_agent_ready else "uninitialized",
            },
        }

    async def get_full_health(self) -> Dict[str, Any]:
        """
        Executes concurrent health checks for all components and evaluates system state.
        Overall status:
          - 'healthy': Postgres, Redis, and MongoDB are healthy
          - 'degraded': At least one non-fatal service has degraded/unhealthy status
          - 'unhealthy': Core database (PostgreSQL) is unreachable
        """
        # Run dependent checks concurrently for low latency
        pg_task = asyncio.create_task(self.check_postgres())
        redis_task = asyncio.create_task(self.check_redis())
        mongo_task = asyncio.create_task(self.check_mongodb())
        rabbit_task = asyncio.create_task(self.check_rabbitmq())

        pg_res, redis_res, mongo_res, rabbit_res = await asyncio.gather(
            pg_task, redis_task, mongo_task, rabbit_task
        )

        agents_res = self.check_agents()
        system_res = self.get_system_metrics()

        services = {
            "postgresql": pg_res,
            "redis": redis_res,
            "mongodb": mongo_res,
            "rabbitmq": rabbit_res,
            "agents": agents_res,
        }

        # Calculate overall system status
        is_pg_ok = pg_res.get("status") == "healthy"
        is_redis_ok = redis_res.get("status") == "healthy"
        is_mongo_ok = mongo_res.get("status") == "healthy"

        if is_pg_ok and is_redis_ok and is_mongo_ok:
            overall_status = "healthy"
        elif not is_pg_ok:
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"

        return {
            "status": overall_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system": system_res,
            "services": services,
        }

    def get_liveness(self) -> Dict[str, Any]:
        """Instant liveness check for orchestrators / load-balancer probes."""
        return {
            "status": "healthy",
            "uptime_seconds": round(self.uptime_seconds, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


health_service = HealthService()
