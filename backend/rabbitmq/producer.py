import json
import logging
import asyncio
from typing import Dict, Any, Optional

from rabbitmq.connection import rabbitConnection, RabbitMQConnection
from Notification.service import notificationService

logger = logging.getLogger(__name__)

DEFAULT_NOTIFICATION_QUEUE = "dukaan_notifications"


class RabbitMQProducer:
    """
    RabbitMQ message producer for background notification tasks.
    Publishes JSON payloads with persistent delivery and graceful direct-dispatch fallback.
    """

    def __init__(
        self,
        connection_manager: Optional[RabbitMQConnection] = None,
        default_queue: str = DEFAULT_NOTIFICATION_QUEUE,
        fallback_to_sync: bool = True,
    ):
        self.connection_manager = connection_manager or rabbitConnection
        self.default_queue = default_queue
        self.fallback_to_sync = fallback_to_sync

    async def publish(
        self,
        message: Dict[str, Any],
        queue_name: Optional[str] = None,
        routing_key: Optional[str] = None,
    ) -> bool:
        """
        Publishes a message to RabbitMQ queue.
        If broker is unreachable and fallback_to_sync is True, dispatches directly.
        """
        target_queue = queue_name or self.default_queue
        target_routing_key = routing_key or target_queue

        try:
            import aio_pika

            channel = await self.connection_manager.get_async_channel()
            if channel:
                # Ensure queue exists and is durable
                queue = await channel.declare_queue(
                    target_queue,
                    durable=True,
                    auto_delete=False,
                )

                body = json.dumps(message, default=str).encode("utf-8")
                pika_message = aio_pika.Message(
                    body=body,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    content_type="application/json",
                )

                await channel.default_exchange.publish(
                    pika_message,
                    routing_key=target_routing_key,
                )
                logger.info(
                    "[RabbitMQ Producer] Published message of type '%s' to queue '%s'",
                    message.get("type", "UNKNOWN"),
                    target_queue,
                )
                return True

        except Exception as e:
            logger.warning(
                "[RabbitMQ Producer] Failed publishing message to RabbitMQ (%s): %s",
                target_queue,
                e,
            )

        # Fallback to direct background dispatch if broker is unreachable
        if self.fallback_to_sync:
            logger.info(
                "[RabbitMQ Producer] Executing direct fallback dispatch for event: %s",
                message.get("type"),
            )
            try:
                # Dispatch in async task so caller is not blocked
                asyncio.create_task(notificationService.dispatch(message))
                return True
            except Exception as dispatch_err:
                logger.error("[RabbitMQ Producer] Fallback dispatch failed: %s", dispatch_err)
                return False

        return False

    async def publish_notification(
        self,
        event_type: str,
        recipient: str,
        data: Dict[str, Any],
        channel: str = "email",
        queue_name: Optional[str] = None,
    ) -> bool:
        """
        Helper method to construct standard notification payload and publish.
        """
        payload: Dict[str, Any] = {
            "type": event_type,
            "channel": channel,
            "recipient": recipient,
            **data,
        }
        return await self.publish(payload, queue_name=queue_name)


# Singleton producer instance
rabbitProducer = RabbitMQProducer()
rabbit_producer = rabbitProducer
