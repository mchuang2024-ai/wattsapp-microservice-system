#!/usr/bin/env python3

"""
Test script to publish a message to RabbitMQ for testing the notification consumer.
"""

import pika
import json

# RabbitMQ settings
amqp_host = "localhost"
amqp_port = 5672
exchange_name = "wattsapp_topic"

# Test message
test_message = {
    "driverID": 1,
    "chat_id": "1146728523",
    "message": "Test notification from RabbitMQ!",
    "type": "test"
}

def publish_message():
    try:
        print(f"Connecting to RabbitMQ at {amqp_host}:{amqp_port}...")
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=amqp_host, port=amqp_port)
        )
        channel = connection.channel()

        # Declare exchange (in case it doesn't exist)
        channel.exchange_declare(
            exchange=exchange_name, exchange_type='topic', durable=True
        )

        # Publish message
        routing_key = "late.test"  # Test routing key
        channel.basic_publish(
            exchange=exchange_name,
            routing_key=routing_key,
            body=json.dumps(test_message)
        )

        print(f"Published test message to exchange '{exchange_name}' with routing key '{routing_key}'")
        print(f"Message: {test_message}")

        connection.close()

    except Exception as e:
        print(f"Error publishing message: {e}")

if __name__ == "__main__":
    publish_message()