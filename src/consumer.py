import json
import logging
from services.redis_service import RedisService
from services.rabbitmq_service import RabbitMQService
from config import settings
import asyncio
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageConsumer:
    def __init__(self):
        self.redis = RedisService()
        self.rabbitmq = RabbitMQService()
        self.loop = asyncio.get_event_loop()

    def process_timing_data(self, ch, method, properties, body):
        """Process timing data messages"""
        try:
            message = json.loads(body)
            logger.info(f"Processing timing data: {message}")

            # Validate message format
            required_fields = ["device_id", "lap_time"]
            if not all(field in message for field in required_fields):
                logger.error(f"Invalid message format: {message}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return

            # Store in Redis
            self.loop.run_until_complete(
                self.redis.store_timing_data(message["device_id"], message)
            )

            # Acknowledge the message
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except json.JSONDecodeError as e:
            logger.error(f"Error decoding message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"Error processing timing data: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def process_sensor_data(self, ch, method, properties, body):
        """Process sensor data messages"""
        try:
            message = json.loads(body)
            logger.info(f"Processing sensor data: {message}")

            # Validate message format
            required_fields = ["device_id", "sensor_type", "value", "unit"]
            if not all(field in message for field in required_fields):
                logger.error(f"Invalid message format: {message}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return

            # Store in Redis
            self.loop.run_until_complete(
                self.redis.store_sensor_data(message["device_id"], message)
            )

            # Acknowledge the message
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except json.JSONDecodeError as e:
            logger.error(f"Error decoding message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"Error processing sensor data: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def run(self):
        """Start consuming messages from both queues"""
        try:
            # Setup consumers for both queues
            self.rabbitmq.consume_messages(
                settings.TIMING_QUEUE, self.process_timing_data
            )
            self.rabbitmq.consume_messages(
                settings.SENSOR_QUEUE, self.process_sensor_data
            )

            logger.info("Started consuming messages from all queues")
            self.rabbitmq.start_consuming()

        except KeyboardInterrupt:
            logger.info("Stopping consumer...")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            self.rabbitmq.close()


if __name__ == "__main__":
    consumer = MessageConsumer()
    consumer.run()
