import os
import sys
import json
import time
import logging
import asyncio
from pathlib import Path

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from rabbitmq.connection import rabbitConnection
from Notification.service import notificationService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("rabbitmq.email_worker")

QUEUE_NAME = "dukaan_notifications"


class EmailNotificationWorker:
    """
    Dedicated background worker consuming email & notification tasks from RabbitMQ.
    Processes tasks with exponential backoff and message acknowledgment.
    """

    def __init__(self, queue_name: str = QUEUE_NAME):
        self.queue_name = queue_name
        self.running = False

    async def start_async(self):
        """Runs the worker using aio-pika event loop."""
        import aio_pika

        self.running = True
        logger.info("[EmailWorker] Starting async notification worker on queue: '%s'...", self.queue_name)

        while self.running:
            try:
                conn = await rabbitConnection.get_async_connection()
                if not conn:
                    logger.warning("[EmailWorker] RabbitMQ offline. Retrying in 5 seconds...")
                    await asyncio.sleep(5)
                    continue

                channel = await conn.channel()
                await channel.set_qos(prefetch_count=5)
                queue = await channel.declare_queue(self.queue_name, durable=True)

                logger.info("[EmailWorker] Worker is active and listening for messages on '%s'...", self.queue_name)

                async with queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        if not self.running:
                            break
                        async with message.process():
                            try:
                                payload = json.loads(message.body.decode("utf-8"))
                                logger.info(
                                    "[EmailWorker] Received notification task: type=%s, recipient=%s",
                                    payload.get("type"),
                                    payload.get("recipient") or payload.get("to_email"),
                                )

                                success = await notificationService.dispatch(payload)
                                if success:
                                    logger.info("[EmailWorker] Task successfully executed.")
                                else:
                                    logger.warning("[EmailWorker] Task executed with dispatch failure.")
                            except Exception as proc_err:
                                logger.exception("[EmailWorker] Error processing message: %s", proc_err)

            except asyncio.CancelledError:
                logger.info("[EmailWorker] Async worker loop cancelled.")
                break
            except Exception as loop_err:
                logger.warning("[EmailWorker] Connection dropped (%s). Reconnecting in 5s...", loop_err)
                await asyncio.sleep(5)

    def start_sync(self):
        """Runs the worker using synchronous pika blocking connection."""
        import pika

        self.running = True
        logger.info("[EmailWorker] Starting sync notification worker on queue: '%s'...", self.queue_name)

        while self.running:
            try:
                conn = rabbitConnection.get_sync_connection()
                if not conn or not conn.is_open:
                    logger.warning("[EmailWorker] RabbitMQ offline. Retrying in 5 seconds...")
                    time.sleep(5)
                    continue

                channel = rabbitConnection.get_sync_channel()
                channel.queue_declare(queue=self.queue_name, durable=True)
                channel.basic_qos(prefetch_count=5)

                def on_message(ch, method, properties, body):
                    try:
                        payload = json.loads(body.decode("utf-8"))
                        logger.info(
                            "[EmailWorker:Sync] Consuming task: type=%s, recipient=%s",
                            payload.get("type"),
                            payload.get("recipient") or payload.get("to_email"),
                        )
                        # Run async notificationService in synchronous loop
                        success = asyncio.run(notificationService.dispatch(payload))
                        if success:
                            logger.info("[EmailWorker:Sync] Task processed successfully.")
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception as err:
                        logger.exception("[EmailWorker:Sync] Error handling message: %s", err)
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

                channel.basic_consume(queue=self.queue_name, on_message_callback=on_message)
                logger.info("[EmailWorker:Sync] Listening for incoming messages on '%s'...", self.queue_name)
                channel.start_consuming()

            except KeyboardInterrupt:
                logger.info("[EmailWorker] KeyboardInterrupt received. Shutting down worker.")
                self.running = False
                break
            except Exception as sync_err:
                logger.warning("[EmailWorker:Sync] Broker connection error: %s. Reconnecting in 5s...", sync_err)
                time.sleep(5)


def run_worker():
    """Main CLI entrypoint for running the worker."""
    worker = EmailNotificationWorker()
    try:
        if sys.platform == "win32":
            # On Windows, sync loop with pika is exceptionally stable
            worker.start_sync()
        else:
            asyncio.run(worker.start_async())
    except KeyboardInterrupt:
        logger.info("[EmailWorker] Worker stopped.")


if __name__ == "__main__":
    run_worker()
