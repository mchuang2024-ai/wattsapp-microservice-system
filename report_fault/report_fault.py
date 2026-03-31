from flask import Flask, request, jsonify
import requests
import os
import pika
import json
from datetime import datetime
import sys
import functools
print = functools.partial(print, flush=True)

app = Flask(__name__)

# service URLs
MAINTENANCE_URL = os.environ.get('MAINTENANCE_URL', 'http://localhost:5005')
BOOKING_URL = os.environ.get('BOOKING_URL', 'http://localhost:5002')
PAYMENT_URL = os.environ.get('PAYMENT_URL', 'http://localhost:5003')
NOTIFICATION_URL = os.environ.get('NOTIFICATION_URL', 'http://localhost:5004')
STATUS_URL = os.environ.get('STATUS_URL', 'https://personal-dftp1xlj.outsystemscloud.com/Status/rest/Status')

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
        
        # Publish charger.fault.reported event
        publish_event('charger.fault.reported', {
            'event_type': 'charger.fault.reported',
            'booking_id': bookingID,
            'slot_id': slotID,
            'driver_id': driverID,
            'description': description,
            'ticket_id': ticket_id,
            'timestamp': datetime.now().isoformat()
        })

        # Refund user
        print(f"[3] Attempting refund for driver {driverID}...")
        try:
            resp = requests.post(f"{PAYMENT_URL}/payment/forfeit-deposit", json={
                "bookingID": bookingID,
                "driverID": driverID,
            }, timeout=2)
            results.append({"step": "refund", "status": resp.status_code})
            print(f"    ✓ Refund successful: {resp.status_code}")
        except requests.exceptions.ConnectionError:
            results.append({"step": "refund", "status": "skipped", "message": "Payment service not available"})
            print(f"    ⚠ Payment service not running - skipping")
        except Exception as e:
            results.append({"step": "refund", "status": "failed", "error": str(e)})
            print(f"    ✗ Refund failed: {e}")

        # Check for affected bookings (NEW STEP)
        print(f"[4] Checking for affected bookings...")
        try:
            resp = requests.get(f"{BOOKING_URL}/booking?slotID={slotID}&status=upcoming", timeout=2)
            if resp.status_code == 200:
                bookings_data = resp.json().get('data', {}).get('bookings', [])
                affected_drivers = [b.get('driverID') for b in bookings_data if b.get('driverID') != driverID]
                results.append({"step": "check_affected", "status": resp.status_code, "count": len(affected_drivers)})
                print(f"    ✓ Found {len(affected_drivers)} affected drivers")
                
                if affected_drivers:
                    publish_event('charger.fault.affected', {
                        'event_type': 'charger.fault.affected',
                        'slot_id': slotID,
                        'affected_drivers': affected_drivers,
                        'timestamp': datetime.now().isoformat()
                    })
        except Exception as e:
            results.append({"step": "check_affected", "status": "skipped", "error": str(e)})
            print(f"    ⚠ Could not check affected bookings: {e}")

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
                    'booking_id': bookingID,
                    'driver_id': driverID,
                    'slot_id': slotID,
                    'reason': 'faulty_charger',
                    'timestamp': datetime.now().isoformat()
                })
        except requests.exceptions.ConnectionError:
            results.append({"step": "cancel_booking", "status": "skipped", "message": "Booking service not available"})
            print(f"    ⚠ Booking service not running - skipping")
        except Exception as e:
            results.append({"step": "cancel_booking", "status": "failed", "error": str(e)})
            print(f"    ✗ Cancellation failed: {e}")

        # Send notification
        print(f"[6] Attempting to send notification to driver {driverID}...")
        try:
            resp = requests.post(f"{NOTIFICATION_URL}/notification/send", json={
                "driverID": driverID,
                "message": "Your booking was cancelled due to faulty charger.",
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