from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import requests
import pika
import json
import traceback
from datetime import datetime

import config
from models import db, BookingLog

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)

# init SQLAlchemy (optional)
db.init_app(app)


def publish_booking_created(booking_id, slot_id, driver_id):
    # Fetch driver's Telegram chat ID so the notification consumer can send a message
    chat_id = None
    try:
        driver_resp = requests.get(f"{config.DRIVER_URL}/drivers/{driver_id}", timeout=5)
        if driver_resp.status_code == 200:
            driver_data = driver_resp.json().get('data', {})
            chat_id = driver_data.get('telegram_chat_id')
    except Exception as e:
        print(f"Could not fetch driver info for notification: {e}")

    params = {
        'driverID': driver_id,
        'chat_id': str(chat_id) if chat_id else None,
        'message': f'Your booking #{booking_id} at slot {slot_id} has been confirmed! Thank you for using PulsePark.',
        'type': 'booking',
        'bookingID': booking_id,
        'slotID': slot_id,
        'station': 'Sengkang Hub'
    }
    connection = pika.BlockingConnection(pika.URLParameters(config.RABBITMQ_URL))
    channel = connection.channel()
    channel.exchange_declare(exchange='wattsapp_topic', exchange_type='topic', durable=True)
    channel.basic_publish(
        exchange='wattsapp_topic',
        routing_key='booking.created',
        body=json.dumps(params),
        properties=pika.BasicProperties(content_type='application/json', delivery_mode=2)
    )
    connection.close()
    print(f"Event published: booking.created")


@app.route('/create-booking', methods=['POST'])
def create_booking():
    if not request.is_json:
        return jsonify({'error': 'Invalid JSON'}), 400

    data = request.get_json()
    required = ['driverID', 'chargerID', 'starttime', 'endtime', 'deposit']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400

    driver_id = data['driverID']
    charger_id = data['chargerID']
    try:
        charger_id = int(charger_id)
    except (ValueError, TypeError):
        pass
    starttime = data['starttime']
    endtime = data['endtime']
    deposit = data['deposit']

    # 2. Payment hold
    try:
        payment_resp = requests.post(
            config.PAYMENT_URL,
            json={'driverID': int(driver_id), 'bookingID': 0, 'amount': float(deposit)},
            timeout=10
        )
        if payment_resp.status_code not in (200, 201):
            err_body = payment_resp.text
            print(f"Payment authorization failed [{payment_resp.status_code}]: {err_body}")
            return jsonify({'error': f'Payment authorization failed ({payment_resp.status_code})', 'detail': err_body}), 500
    except Exception as e:
        print(f"Payment service error: {e}")
        return jsonify({'error': 'Payment service unreachable', 'details': str(e)}), 500

    # 3. Booking creation
    try:
        booking_resp = requests.post(
            config.BOOKING_URL,
            json={
                'driverID': driver_id,
                'slotID': charger_id,
                'startTime': starttime.replace('T', ' '),
                'endTime': endtime.replace('T', ' ')
            },
            timeout=10
        )
        if booking_resp.status_code not in (200, 201):
            # rollback payment hold
            try:
                requests.post(f"{config.PAYMENT_URL.replace('/payment/hold', '/payment/release')}",
                              json={'driverID': driver_id, 'deposit': deposit}, timeout=10)
            except Exception as e2:
                print(f"Failed rollback payment: {e2}")
            return jsonify({'error': 'Booking creation failed'}), 500
    except Exception as e:
        print(f"Booking service error: {e}")
        try:
            requests.post(f"{config.PAYMENT_URL.replace('/payment/hold', '/payment/release')}",
                          json={'driverID': driver_id, 'deposit': deposit}, timeout=10)
        except Exception as e2:
            print(f"Failed rollback payment: {e2}")
        return jsonify({'error': 'Booking creation failed', 'details': str(e)}), 500

    booking_data = booking_resp.json() if booking_resp.content else {}
    # booking service returns {"code": 201, "data": {"bookingID": ...}}
    inner = booking_data.get('data', booking_data)
    booking_id = inner.get('bookingID') or inner.get('id') or booking_data.get('bookingID') or None

    if not booking_id:
        try:
            requests.post(f"{config.PAYMENT_URL.replace('/payment/hold', '/payment/release')}",
                          json={'driverID': driver_id, 'deposit': deposit}, timeout=10)
        except Exception as e2:
            print(f"Failed rollback payment: {e2}")
        return jsonify({'error': 'Booking service did not return bookingID'}), 500

    # 4. Publish event to RabbitMQ
    try:
        publish_booking_created(booking_id, charger_id, driver_id)
    except Exception as e:
        print(f"RabbitMQ publish error: {e}")

    # 5. Optional DB log
    try:
        with app.app_context():
            log = BookingLog(
                driverID=driver_id,
                chargerID=charger_id,
                starttime=datetime.fromisoformat(starttime),
                endtime=datetime.fromisoformat(endtime),
                deposit=deposit,
                bookingID=booking_id
            )
            db.session.add(log)
            db.session.commit()
    except Exception as e:
        print(f"Optional DB log error: {e}")
        db.session.rollback()

    print(f"Booking created: {booking_id}")

    return jsonify({
        'status': 'confirmed',
        'bookingID': booking_id,
        'message': 'Slot reserved successfully'
    }), 200


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal Server Error', 'details': str(error)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5011, debug=True)
