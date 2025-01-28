import pika

# RabbitMQ configuration
RABBITMQ_HOST = "localhost"
RABBITMQ_PORT = 5672
RABBITMQ_USER = "user"
RABBITMQ_PASS = "password"
RABBITMQ_QUEUE = "dummy_queue"

# Connect to RabbitMQ
credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        virtual_host="/",
        credentials=credentials,
    )
)
channel = connection.channel()

# Declare the queue
channel.queue_declare(queue=RABBITMQ_QUEUE)

# Messages to send
messages = ["Hello, RabbitMQ!", "Second Message", "Another Message"]

# Publish messages
for message in messages:
    channel.basic_publish(exchange="", routing_key=RABBITMQ_QUEUE, body=message)
    print(f"Published message: {message}")

# Close the connection
connection.close()
print("All messages published successfully!")
