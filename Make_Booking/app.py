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
    params = {
        'bookingID': booking_id,
        'slotID': slot_id,
        'driverID': driver_id,
        'station': 'Sengkang Hub'
    }
    connection = pika.BlockingConnection(pika.URLParameters('amqp://admin:password123@rabbitmq:5672/'))
    channel = connection.channel()
    channel.exchange_declare(exchange='pulsepark.events', exchange_type='topic', durable=True)
    channel.basic_publish(
        exchange='pulsepark.events',
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
    starttime = data['starttime']
    endtime = data['endtime']
    deposit = data['deposit']

    # 2. Payment hold
    try:
        payment_resp = requests.post(
            config.PAYMENT_URL,
            json={'driverID': driver_id, 'deposit': deposit},
            timeout=10
        )
        if payment_resp.status_code not in (200, 201):
            print("Payment authorization failed", payment_resp.text)
            return jsonify({'error': 'Payment authorization failed'}), 500
    except Exception as e:
        print(f"Payment service error: {e}")
        return jsonify({'error': 'Payment authorization failed', 'details': str(e)}), 500

    # 3. Booking creation
    try:
        booking_resp = requests.post(
            config.BOOKING_URL,
            json={
                'driverID': driver_id,
                'slotID': charger_id,
                'startTime': starttime,
                'endTime': endtime
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
    booking_id = booking_data.get('bookingID') or booking_data.get('id') or None

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
