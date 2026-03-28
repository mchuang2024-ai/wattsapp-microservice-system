from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# service URLs
MAINTENANCE_URL = os.environ.get('MAINTENANCE_URL', 'http://localhost:5005')
BOOKING_URL = os.environ.get('BOOKING_URL', 'http://localhost:5002')
PAYMENT_URL = os.environ.get('PAYMENT_URL', 'http://localhost:5003')
NOTIFICATION_URL = os.environ.get('NOTIFICATION_URL', 'http://localhost:5004')
STATUS_URL = os.environ.get('STATUS_URL', 'https://personal-dftp1xlj.outsystemscloud.com/Status/rest/Status')

@app.route("/reportfault", methods=['POST'])
def report_fault():
    data = request.get_json()

    bookingID = data.get("bookingID")
    slotID = data.get("slotID")
    driverID = data.get("driverID")
    description = data.get("description")

    results = []

    try:
        # 1. Mark charger as faulty
        print(f"[1] Updating slot {slotID} to faulty...")
        resp = requests.put(f"{STATUS_URL}/status/{slotID}", json={"status": "faulty"})
        results.append({"step": "update_status", "status": resp.status_code})
        print(f"    ✓ Status: {resp.status_code}")

        # 2. Create maintenance ticket
        print(f"[2] Creating maintenance ticket for slot {slotID}...")
        resp = requests.post(f"{MAINTENANCE_URL}/maintenance/ticket", json={
            "slotID": slotID,
            "reportedBy": driverID,
            "description": description,
            "chargerType": "fast"
        })
        results.append({"step": "create_ticket", "status": resp.status_code})
        print(f"    ✓ Status: {resp.status_code}")

        # 3. Refund user
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

        # 4. Cancel booking
        print(f"[4] Attempting to cancel booking {bookingID}...")
        try:
            resp = requests.delete(f"{BOOKING_URL}/booking/{bookingID}", timeout=2)
            results.append({"step": "cancel_booking", "status": resp.status_code})
            print(f"    ✓ Booking cancelled: {resp.status_code}")
        except requests.exceptions.ConnectionError:
            results.append({"step": "cancel_booking", "status": "skipped", "message": "Booking service not available"})
            print(f"    ⚠ Booking service not running - skipping")
        except Exception as e:
            results.append({"step": "cancel_booking", "status": "failed", "error": str(e)})
            print(f"    ✗ Cancellation failed: {e}")

        # 5. Send notification
        print(f"[5] Attempting to send notification to driver {driverID}...")
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