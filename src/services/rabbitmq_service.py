import pika
import json
import logging
from typing import Callable, Any, Dict
from config import settings
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class RabbitMQService:
    def __init__(self):
        self.credentials = pika.PlainCredentials(
            settings.RABBITMQ_USER, settings.RABBITMQ_PASS
        )
        self.connection = None
        self.channel = None
        self.connect()

    def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            parameters = pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                credentials=self.credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
                connection_attempts=3,
                retry_delay=5,
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # Declare exchanges
            self.channel.exchange_declare(
                exchange="livetiming", exchange_type="topic", durable=True
            )

            # Declare queues
            self._declare_queues()

            logger.info("Successfully connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def _declare_queues(self):
        """Declare all necessary queues and their bindings"""
        # Timing data queue
        self.channel.queue_declare(
            queue=settings.TIMING_QUEUE,
            durable=True,
            arguments={
                "x-message-ttl": 86400000,  # 24 hours
                "x-max-length": 10000,
                "x-overflow": "reject-publish",
            },
        )
        self.channel.queue_bind(
            exchange="livetiming", queue=settings.TIMING_QUEUE, routing_key="timing.#"
        )

        # Sensor data queue
        self.channel.queue_declare(
            queue=settings.SENSOR_QUEUE,
            durable=True,
            arguments={
                "x-message-ttl": 86400000,  # 24 hours
                "x-max-length": 10000,
                "x-overflow": "reject-publish",
            },
        )
        self.channel.queue_bind(
            exchange="livetiming", queue=settings.SENSOR_QUEUE, routing_key="sensor.#"
        )

    @contextmanager
    def channel_context(self):
        """Context manager for channel operations"""
        try:
            if not self.connection or self.connection.is_closed:
                self.connect()
            yield self.channel
        except pika.exceptions.AMQPConnectionError:
            logger.error("Lost connection to RabbitMQ, reconnecting...")
            self.connect()
            yield self.channel
        except Exception as e:
            logger.error(f"Channel operation error: {e}")
            raise

    def publish_message(self, routing_key: str, message: Dict[str, Any]) -> bool:
        """
        Publish message using the topic exchange

        Args:
            routing_key: Format should be either 'timing.{device_id}' or 'sensor.{device_id}.{sensor_type}'
            message: Dictionary containing the message data
        """
        try:
            with self.channel_context() as channel:
                channel.basic_publish(
                    exchange="livetiming",
                    routing_key=routing_key,
                    body=json.dumps(message),
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # make message persistent
                        content_type="application/json",
                        timestamp=int(time.time()),
                    ),
                )
            return True
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return False

    def consume_messages(self, queue: str, callback: Callable):
        """Set up consumer for specified queue with automatic reconnection"""
        while True:
            try:
                with self.channel_context() as channel:
                    channel.basic_qos(prefetch_count=1)
                    channel.basic_consume(
                        queue=queue, on_message_callback=self._wrap_callback(callback)
                    )
                    logger.info(f"Started consuming from queue: {queue}")
                    channel.start_consuming()
            except pika.exceptions.AMQPConnectionError:
                logger.error("Lost connection to RabbitMQ, reconnecting...")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Consumer error: {e}")
                time.sleep(5)

    def _wrap_callback(self, callback: Callable) -> Callable:
        """Wrap the callback to handle errors and reconnection"""

        def wrapped_callback(ch, method, properties, body):
            try:
                callback(ch, method, properties, body)
            except Exception as e:
                logger.error(f"Error in callback: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        return wrapped_callback

    def create_queue_binding(self, queue: str, routing_key: str):
        """Create a new queue binding"""
        with self.channel_context() as channel:
            channel.queue_bind(
                exchange="livetiming", queue=queue, routing_key=routing_key
            )

    def remove_queue_binding(self, queue: str, routing_key: str):
        """Remove a queue binding"""
        with self.channel_context() as channel:
            channel.queue_unbind(
                exchange="livetiming", queue=queue, routing_key=routing_key
            )

    def purge_queue(self, queue: str):
        """Purge all messages from a queue"""
        with self.channel_context() as channel:
            channel.queue_purge(queue=queue)

    def get_queue_message_count(self, queue: str) -> int:
        """Get the number of messages in a queue"""
        with self.channel_context() as channel:
            response = channel.queue_declare(queue=queue, passive=True)
            return response.method.message_count

    def close(self):
        """Close RabbitMQ connection"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")
