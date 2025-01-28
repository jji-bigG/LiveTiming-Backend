import os
import redis
import pika

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# RabbitMQ configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")

# Dummy data
REDIS_DUMMY_DATA = {"key1": "value1", "key2": "value2", "key3": "value3"}
RABBITMQ_QUEUE = "dummy_queue"
RABBITMQ_MESSAGES = ["Message 1", "Message 2", "Message 3"]


def load_redis():
    print("Loading data into Redis...")
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    for key, value in REDIS_DUMMY_DATA.items():
        r.set(key, value)
        print(f"Set {key}: {value}")


def load_rabbitmq():
    print("Publishing messages to RabbitMQ...")
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials
        )
    )
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE)

    for message in RABBITMQ_MESSAGES:
        channel.basic_publish(exchange="", routing_key=RABBITMQ_QUEUE, body=message)
        print(f"Published: {message}")

    connection.close()


if __name__ == "__main__":
    load_redis()
    load_rabbitmq()
