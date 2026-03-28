"""
notification_amqp.py — AMQP consumer for the Notification microservice.

Runs as a separate process alongside notification.py.
Subscribes to the 'notification_queue' on the 'wattsapp_topic' exchange.
The queue is pre-created by rabbitmq/amqp_setup.py with routing key '#'.

Expected single-driver message format:
{
    "driverID": 1,
    "chat_id": "634243561",
    "message": "Your booking is confirmed!",
    "type": "booking"
}

Expected broadcast (waitlist) message format:
{
    "drivers": [
        {"driverID": 1, "chat_id": "634243561"},
        {"driverID": 2, "chat_id": "483102075"}
    ],
    "message": "A slot has opened!",
    "type": "waitlist"
}
"""

import json
import os

import amqp_lib
from notification import app, db, Notification, send_telegram_message

# ── RabbitMQ configuration ─────────────────────────────────────────────────
# Override via environment variables (set automatically by docker-compose)
RABBIT_HOST   = os.environ.get("RABBITMQ_HOST", "localhost")
RABBIT_PORT   = int(os.environ.get("RABBITMQ_PORT", 5672))
RABBIT_USER   = os.environ.get("RABBITMQ_USER", "admin")
RABBIT_PASS   = os.environ.get("RABBITMQ_PASS", "password123")
EXCHANGE_NAME = "wattsapp_topic"
EXCHANGE_TYPE = "topic"
QUEUE_NAME    = "notification_queue"


# ── Helpers ────────────────────────────────────────────────────────────────

def process_notification(driver_id, chat_id, message, notif_type):
    """Send a Telegram message and log the result to the database."""
    telegram_status = "sent"

    if chat_id:
        success, _ = send_telegram_message(str(chat_id), message)
        if not success:
            telegram_status = "failed"
    else:
        telegram_status = "failed"

    with app.app_context():
        notification = Notification(
            driverID=driver_id,
            message=message,
            type=notif_type,
            status=telegram_status,
        )
        try:
            db.session.add(notification)
            db.session.commit()
            print(
                f"[AMQP] Logged — driverID={driver_id}, "
                f"type={notif_type}, status={telegram_status}"
            )
        except Exception as e:
            db.session.rollback()
            print(f"[AMQP] DB error: {e}")


# ── Callback ───────────────────────────────────────────────────────────────

def callback(channel, method, properties, body):
    print(f"[AMQP] Received message (routing key: {method.routing_key})")

    try:
        data = json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, TypeError) as e:
        print(f"[AMQP] Failed to decode message body: {e}")
        return

    notif_type = data.get("type", "unknown")
    message    = data.get("message", "")

    # Broadcast format (e.g. waitlist — multiple drivers)
    if "drivers" in data:
        drivers = data["drivers"]
        print(f"[AMQP] Broadcasting to {len(drivers)} driver(s) — type={notif_type}")
        for driver in drivers:
            process_notification(
                driver_id=driver.get("driverID"),
                chat_id=driver.get("chat_id"),
                message=message,
                notif_type=notif_type,
            )

    # Single-driver format
    else:
        process_notification(
            driver_id=data.get("driverID"),
            chat_id=data.get("chat_id"),
            message=message,
            notif_type=notif_type,
        )


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  Notification AMQP Consumer starting...")
    print(f"  RabbitMQ : {RABBIT_HOST}:{RABBIT_PORT}")
    print(f"  Exchange : {EXCHANGE_NAME} ({EXCHANGE_TYPE})")
    print(f"  Queue    : {QUEUE_NAME}")
    print("  NOTE: Queue must be pre-created via rabbitmq/amqp_setup.py")
    print("=" * 55)

    connection = None
    while True:
        try:
            connection, channel = amqp_lib.connect(
                hostname=RABBIT_HOST,
                port=RABBIT_PORT,
                exchange_name=EXCHANGE_NAME,
                exchange_type=EXCHANGE_TYPE,
                username=RABBIT_USER,
                password=RABBIT_PASS,
            )
            print(f"[AMQP] Consuming from queue: {QUEUE_NAME}")
            channel.basic_consume(
                queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True
            )
            channel.start_consuming()

        except amqp_lib.pika.exceptions.ConnectionClosedByBroker:
            print("[AMQP] Connection closed. Reconnecting...")
            continue

        except KeyboardInterrupt:
            if connection:
                amqp_lib.close(connection, channel)
            break
