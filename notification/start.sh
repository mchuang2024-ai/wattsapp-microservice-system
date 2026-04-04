#!/bin/sh
# Wait for RabbitMQ to be ready, then create exchange/queues
echo "Running amqp_setup.py..."
until python amqp_setup.py; do
    echo "amqp_setup.py failed (RabbitMQ not ready?). Retrying in 5s..."
    sleep 5
done
echo "amqp_setup.py succeeded."

# Start HTTP server in background
python notification.py &

# Start AMQP consumer in foreground (keeps container alive)
python notification_amqp.py
