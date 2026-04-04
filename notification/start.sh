#!/bin/sh
# Create RabbitMQ exchange and queues
python rabbitmq/amqp_setup.py

# Start HTTP server in background
python notification.py &

# Start AMQP consumer in foreground (keeps container alive)
python notification_amqp.py
