#!/usr/bin/env python3

"""
AMQP consumer for Notification microservice.
Subscribes to wattsapp_topic exchange and processes notification events.
"""

import pika
import requests
import json
import os

# RabbitMQ settings
amqp_host = os.environ.get('AMQP_HOST', 'localhost')
amqp_port = int(os.environ.get('AMQP_PORT', 5672))
exchange_name = "wattsapp_topic"
queue_name = "notification_queue"

# Notification service URL
notification_url = os.environ.get('NOTIFICATION_URL', 'http://localhost:5005/notification/send')


def callback(ch, method, properties, body):
    """
    Callback function when a message is received.
    Processes the notification event and sends it via the notification service.
    """
    try:
        # Parse the message
        message_data = json.loads(body.decode('utf-8'))
        routing_key = method.routing_key

        print(f"Received message with routing key '{routing_key}': {message_data}")

        # Validate required fields
        if not all(key in message_data for key in ['message', 'type']):
            print("Invalid message format: missing 'message' or 'type'")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # Send to notification service
        response = requests.post(notification_url, json=message_data)

        if response.status_code == 201:
            print(f"Notification sent successfully: {response.json()}")
        else:
            print(f"Failed to send notification: {response.status_code} - {response.text}")

    except json.JSONDecodeError:
        print("Invalid JSON in message")
    except Exception as e:
        print(f"Error processing message: {e}")
    finally:
        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    try:
        print(f"Connecting to AMQP broker {amqp_host}:{amqp_port}...")
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=amqp_host,
                port=amqp_port,
                heartbeat=300,
                blocked_connection_timeout=300,
            )
        )
        print("Connected")

        channel = connection.channel()

        # Declare exchange (in case it doesn't exist)
        channel.exchange_declare(
            exchange=exchange_name, exchange_type='topic', durable=True
        )

        # Declare queue
        channel.queue_declare(queue=queue_name, durable=True)

        # Bind queue to exchange with routing key
        channel.queue_bind(
            exchange=exchange_name, queue=queue_name, routing_key='#'
        )

        print(f"Consuming from queue '{queue_name}'...")

        # Set up consumer
        channel.basic_consume(
            queue=queue_name, on_message_callback=callback, auto_ack=False
        )

        # Start consuming
        channel.start_consuming()

    except KeyboardInterrupt:
        print("Consumer stopped by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'connection' in locals() and connection.is_open:
            connection.close()
            print("Connection closed")


if __name__ == "__main__":
    main()