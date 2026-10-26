import os
import logging
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Ensure .env is loaded
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

logger = logging.getLogger(__name__)


class RabbitMQConnection:
    """
    RabbitMQ connection manager supporting both aio-pika (async) and pika (sync).
    Provides resilient connection lifecycle, reconnect logic, and graceful degradation.
    """

    def __init__(self, amqp_url: Optional[str] = None):
        self.amqp_url = amqp_url or os.getenv("RABBITMQ_URL") or "amqp://guest:guest@localhost:5672/"
        self._async_connection = None
        self._async_channel = None
        self._sync_connection = None
        self._sync_channel = None
        self._is_available: Optional[bool] = None

    @property
    def url(self) -> str:
        return os.getenv("RABBITMQ_URL") or self.amqp_url

    async def get_async_connection(self):
        """Returns active aio-pika robust connection, establishing it if necessary."""
        import aio_pika

        if self._async_connection and not self._async_connection.is_closed:
            return self._async_connection

        try:
            self._async_connection = await aio_pika.connect_robust(
                self.url,
                timeout=5.0,
            )
            self._is_available = True
            logger.info("[RabbitMQ] Async robust connection established successfully.")
            return self._async_connection
        except Exception as e:
            self._is_available = False
            logger.warning("[RabbitMQ] Could not connect to RabbitMQ at %s: %s", self.url, e)
            return None

    async def get_async_channel(self):
        """Returns active aio-pika channel, declaring connection if necessary."""
        if self._async_channel and not self._async_channel.is_closed:
            return self._async_channel

        conn = await self.get_async_connection()
        if not conn:
            return None

        try:
            self._async_channel = await conn.channel()
            # Set default prefetch count for fair dispatch
            await self._async_channel.set_qos(prefetch_count=10)
            return self._async_channel
        except Exception as e:
            logger.warning("[RabbitMQ] Failed opening async channel: %s", e)
            return None

    def get_sync_connection(self):
        """Returns active pika blocking connection (used primarily by workers)."""
        import pika

        if self._sync_connection and self._sync_connection.is_open:
            return self._sync_connection

        try:
            parameters = pika.URLParameters(self.url)
            parameters.connection_attempts = 3
            parameters.retry_delay = 2
            parameters.socket_timeout = 10
            self._sync_connection = pika.BlockingConnection(parameters)
            self._is_available = True
            logger.info("[RabbitMQ] Sync BlockingConnection established successfully.")
            return self._sync_connection
        except Exception as e:
            self._is_available = False
            logger.warning("[RabbitMQ] Sync connection failed to %s: %s", self.url, e)
            return None

    def get_sync_channel(self):
        """Returns active pika blocking channel."""
        if self._sync_channel and self._sync_channel.is_open:
            return self._sync_channel

        conn = self.get_sync_connection()
        if not conn:
            return None

        try:
            self._sync_channel = conn.channel()
            return self._sync_channel
        except Exception as e:
            logger.warning("[RabbitMQ] Failed opening sync channel: %s", e)
            return None

    async def close_async(self):
        """Gracefully closes async channel and connection."""
        try:
            if self._async_channel and not self._async_channel.is_closed:
                await self._async_channel.close()
            if self._async_connection and not self._async_connection.is_closed:
                await self._async_connection.close()
        except Exception as e:
            logger.debug("[RabbitMQ] Error while closing async connection: %s", e)

    def close_sync(self):
        """Gracefully closes sync channel and connection."""
        try:
            if self._sync_channel and self._sync_channel.is_open:
                self._sync_channel.close()
            if self._sync_connection and self._sync_connection.is_open:
                self._sync_connection.close()
        except Exception as e:
            logger.debug("[RabbitMQ] Error while closing sync connection: %s", e)


# Singleton connection manager
rabbitConnection = RabbitMQConnection()
rabbit_connection = rabbitConnection
