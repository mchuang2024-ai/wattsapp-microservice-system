from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import pika
import json
from datetime import datetime
import sys
import functools
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
print = functools.partial(print, flush=True)

app = Flask(__name__)
CORS(app)

# service URLs
MAINTENANCE_URL = os.environ.get('MAINTENANCE_URL', 'http://localhost:5005')
BOOKING_URL = os.environ.get('BOOKING_URL', 'http://localhost:5002')
PAYMENT_URL = os.environ.get('PAYMENT_URL', 'http://localhost:5003')
NOTIFICATION_URL = os.environ.get('NOTIFICATION_URL', 'http://localhost:5004')
STATUS_URL = os.environ.get('STATUS_URL', 'https://personal-dftp1xlj.outsystemscloud.com/Status/rest/Status')
MAINTENANCE_CHAT_ID = os.environ.get('MAINTENANCE_CHAT_ID', '634243561')  # fallback to Caylern's chat

# RabbitMQ config
RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.environ.get('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.environ.get('RABBITMQ_USER', 'admin')
RABBITMQ_PASS = os.environ.get('RABBITMQ_PASS', 'password123')

def publish_event(routing_key, event_data):
    """Publish event to RabbitMQ"""
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials)
        )
        channel = connection.channel()
        channel.exchange_declare(exchange='wattsapp_topic', exchange_type='topic', durable=True)
        channel.basic_publish(
            exchange='wattsapp_topic',
            routing_key=routing_key,
            body=json.dumps(event_data),
            properties=pika.BasicProperties(content_type='application/json', delivery_mode=2)
        )
        connection.close()
        print(f"    ✓ Published event: {routing_key}")
        return True
    except Exception as e:
        print(f"    ✗ Failed to publish event: {e}")
        return False

@app.route("/reportfault", methods=['POST'])
def report_fault():
    data = request.get_json()

    bookingID = data.get("bookingID")
    slotID = data.get("slotID")
    driverID = data.get("driverID")
    description = data.get("description")

    results = []

    # Look up reporting driver's chat_id for notifications
    DRIVER_URL = os.environ.get('DRIVER_URL', 'http://localhost:5001')
    reporter_chat_id = None
    try:
        driver_resp = requests.get(f"{DRIVER_URL}/drivers/{driverID}", timeout=3)
        if driver_resp.status_code == 200:
            reporter_chat_id = driver_resp.json().get('data', {}).get('telegram_chat_id')
    except Exception:
        pass

    try:
        # Mark charger as faulty
        print(f"[1] Updating slot {slotID} to faulty...")
        resp = requests.put(f"{STATUS_URL}/status/{slotID}", json={"status": "faulty"})
        results.append({"step": "update_status", "status": resp.status_code})
        print(f"    ✓ Status: {resp.status_code}")

        # Create maintenance ticket
        print(f"[2] Creating maintenance ticket for slot {slotID}...")
        resp = requests.post(f"{MAINTENANCE_URL}/maintenance/ticket", json={
            "slotID": slotID,
            "reportedBy": driverID,
            "description": description,
            "chargerType": "fast"
        })
        results.append({"step": "create_ticket", "status": resp.status_code})
        print(f"    ✓ Status: {resp.status_code}")

        # Get ticket ID and publish event
        ticket_id = None
        if resp.status_code == 201:
            ticket_data = resp.json().get('data', {})
            ticket_id = ticket_data.get('ticketID')
        
        # Publish charger.fault.reported event — also notifies maintenance team
        publish_event('charger.fault.reported', {
            'event_type': 'charger.fault.reported',
            'driverID': MAINTENANCE_CHAT_ID,   # route to maintenance team
            'chat_id': MAINTENANCE_CHAT_ID,
            'type': 'fault',
            'bookingID': bookingID,
            'slotID': slotID,
            'ticket_id': ticket_id,
            'message': f"[Maintenance Alert] Fault reported for Slot {slotID}. Ticket #{ticket_id} created. Description: {description}",
            'timestamp': datetime.now().isoformat()
        })

        # Refund user
        print(f"[3] Attempting refund for driver {driverID}...")
        try:
            resp = requests.post(f"{PAYMENT_URL}/payment/refund", json={
                "bookingID": bookingID,
                "driverID": driverID,
                "amount": 5.0,
            }, timeout=2)
            results.append({"step": "refund", "status": resp.status_code})
            print(f"    ✓ Refund successful: {resp.status_code}")
        except requests.exceptions.ConnectionError:
            results.append({"step": "refund", "status": "skipped", "message": "Payment service not available"})
            print(f"    ⚠ Payment service not running - skipping")
        except Exception as e:
            results.append({"step": "refund", "status": "failed", "error": str(e)})
            print(f"    ✗ Refund failed: {e}")

        # Cancel all other active/confirmed bookings for this slot and notify affected drivers
        print(f"[4] Cancelling affected bookings for slot {slotID}...")
        try:
            resp = requests.get(f"{BOOKING_URL}/booking/slot/{slotID}", timeout=2)
            if resp.status_code == 200:
                bookings_data = resp.json().get('data', {}).get('bookings', [])
                affected = [b for b in bookings_data
                            if b.get('status') in ('confirmed', 'pending', 'active', 'checked-in')
                            and str(b.get('driverID')) != str(driverID)]
                results.append({"step": "check_affected", "status": 200, "count": len(affected)})
                print(f"    ✓ Found {len(affected)} affected bookings")
                for b in affected:
                    b_id = b.get('bookingID')
                    b_driver = b.get('driverID')
                    try:
                        requests.put(f"{BOOKING_URL}/booking/{b_id}/cancel", timeout=2)
                        print(f"    ✓ Cancelled booking {b_id} for driver {b_driver}")
                    except Exception:
                        pass
                    publish_event('charger.fault.affected', {
                        'event_type': 'charger.fault.affected',
                        'driverID': b_driver,
                        'type': 'fault',
                        'bookingID': b_id,
                        'slotID': slotID,
                        'message': f"Your upcoming booking (#{b_id}) for Slot {slotID} has been cancelled — the charger is under maintenance. Please rebook another slot.",
                        'timestamp': datetime.now().isoformat()
                    })
        except Exception as e:
            results.append({"step": "check_affected", "status": "skipped", "error": str(e)})
            print(f"    ⚠ Could not cancel affected bookings: {e}")

        # Cancel booking
        print(f"[5] Attempting to cancel booking {bookingID}...")
        try:
            resp = requests.delete(f"{BOOKING_URL}/booking/{bookingID}", timeout=2)
            results.append({"step": "cancel_booking", "status": resp.status_code})
            print(f"    ✓ Booking cancelled: {resp.status_code}")
                        # Publish booking.cancelled event
            if resp.status_code == 200:
                publish_event('booking.cancelled', {
                    'event_type': 'booking.cancelled',
                    'driverID': driverID,
                    'type': 'fault',
                    'bookingID': bookingID,
                    'slotID': slotID,
                    'message': f"Your booking (#{bookingID}) for Slot {slotID} has been cancelled due to a faulty charger. Your deposit has been refunded.",
                    'timestamp': datetime.now().isoformat()
                })
        except requests.exceptions.ConnectionError:
            results.append({"step": "cancel_booking", "status": "skipped", "message": "Booking service not available"})
            print(f"    ⚠ Booking service not running - skipping")
        except Exception as e:
            results.append({"step": "cancel_booking", "status": "failed", "error": str(e)})
            print(f"    ✗ Cancellation failed: {e}")

        # Send notification to reporting driver
        print(f"[6] Attempting to send notification to driver {driverID}...")
        try:
            resp = requests.post(f"{NOTIFICATION_URL}/notification/send", json={
                "driverID": driverID,
                "chat_id": reporter_chat_id or MAINTENANCE_CHAT_ID,
                "message": f"Your booking (#{bookingID}) for Slot {slotID} has been cancelled due to a faulty charger. Your deposit refund has been initiated.",
                "type": "fault"
            }, timeout=2)
            results.append({"step": "notify", "status": resp.status_code})
            print(f"    ✓ Notification sent: {resp.status_code}")
        except requests.exceptions.ConnectionError:
            results.append({"step": "notify", "status": "skipped", "message": "Notification service not available"})
            print(f"    ⚠ Notification service not running - skipping")
        except Exception as e:
            results.append({"step": "notify", "status": "failed", "error": str(e)})
            print(f"    ✗ Notification failed: {e}")

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": str(e),
            "results": results
        }), 500

    return jsonify({
        "code": 200,
        "message": "Fault handled successfully",
        "results": results
    })


@app.route("/health", methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "report-fault"})


if __name__ == "__main__":
    print("=" * 50)
    print("Report Fault Service")
    print("=" * 50)
    print(f"Maintenance: {MAINTENANCE_URL} (REQUIRED)")
    print(f"Status: {STATUS_URL} (REQUIRED)")
    print(f"Notification: {NOTIFICATION_URL} (optional)")
    print(f"Payment: {PAYMENT_URL} (optional)")
    print(f"Booking: {BOOKING_URL} (optional)")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5010, debug=True)