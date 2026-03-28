"""
notification_amqp.py — AMQP consumer for the Notification microservice.

Runs as a separate process alongside notification.py.
Subscribes to the wattsapp_topic exchange and handles all routing keys
that should trigger a notification (booking.*, late.*, slot.*, charger.*, waitlist.*).

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

# ── RabbitMQ configuration (override via environment variables) ────────────
RABBIT_HOST   = os.environ.get("rabbit_host",    "localhost")
RABBIT_PORT   = int(os.environ.get("rabbit_port", 5672))
EXCHANGE_NAME = os.environ.get("exchange_name",  "wattsapp_topic")
EXCHANGE_TYPE = os.environ.get("exchange_type",  "topic")
QUEUE_NAME    = os.environ.get("queue_name",     "Notification")

ROUTING_KEYS  = [
    "booking.*",
    "late.*",
    "slot.*",
    "charger.*",
    "waitlist.*",
]


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
                f"[AMQP] Logged notification — "
                f"driverID={driver_id}, type={notif_type}, status={telegram_status}"
            )
        except Exception as e:
            db.session.rollback()
            print(f"[AMQP] DB error: {e}")


# ── Callback ───────────────────────────────────────────────────────────────

def callback(channel, method, properties, body):
    print(f"[AMQP] Received message (routing key: {method.routing_key})")

    try:
        data = json.loads(body)
    except (json.JSONDecodeError, TypeError) as e:
        print(f"[AMQP] Failed to decode message body: {e}")
        return

    notif_type = data.get("type", "unknown")
    message    = data.get("message", "")

    # Broadcast format (e.g. waitlist notifications with multiple drivers)
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
    print(f"  Keys     : {', '.join(ROUTING_KEYS)}")
    print("=" * 55)

    # Create connection and declare exchange
    connection, channel = amqp_lib.check_setup(
        RABBIT_HOST, RABBIT_PORT, EXCHANGE_NAME, EXCHANGE_TYPE
    )

    # Declare queue and bind each routing key
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    for routing_key in ROUTING_KEYS:
        channel.queue_bind(
            exchange=EXCHANGE_NAME,
            queue=QUEUE_NAME,
            routing_key=routing_key,
        )
        print(f"  Bound '{QUEUE_NAME}' -> '{routing_key}'")

    # Begin consuming
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=callback,
        auto_ack=True,
    )

    print("\n[AMQP] Waiting for messages. Press CTRL+C to exit.\n")
    channel.start_consuming()
