from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import requests
import os



app = Flask(__name__)



# Railway MySQL connection
# Format: mysql+mysqlconnector://user:password@host:port/database
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('dbURL',
    'mysql+mysqlconnector://root:jpPOaVCbCXnTWjDOBzPtDoRKYwqqiClR@caboose.proxy.rlwy.net:45033/notification')
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8766528831:AAFmXWP5UhrEXaOkvB9VP1ILtnN_oYeUUZc')
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}'

db = SQLAlchemy(app)
CORS(app)

# Create database tables if they don't exist
db_available = True
try:
    with app.app_context():
        db.create_all()
        print("Database tables created successfully.")
except Exception as e:
    print(f"Warning: Could not create database tables: {str(e)}")
    print("The service will continue without database functionality.")
    db_available = False


class Notification(db.Model):
    __tablename__ = 'Notification'

    notificationID = db.Column(db.Integer, autoincrement=True, primary_key=True)
    driverID = db.Column(db.Integer, nullable=True)
    message = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    sentAt = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(10), nullable=False, default='sent')

    def __init__(self, driverID, message, type, status='sent'):
        self.driverID = driverID
        self.message = message
        self.type = type
        self.status = status

    def json(self):
        return {
            "notificationID": self.notificationID,
            "driverID": self.driverID,
            "message": self.message,
            "type": self.type,
            "sentAt": self.sentAt.strftime('%Y-%m-%d %H:%M:%S') if self.sentAt else None,
            "status": self.status
        }


# ==========================================
# Helper: Send message via Telegram Bot API
# ==========================================
def send_telegram_message(chat_id, message):
    """
    Sends a message to a Telegram user/group via the Bot API.
    chat_id: The Telegram chat ID of the recipient.
    message: The text message to send.
    Returns: (success: bool, response_data: dict)
    """
    url = f'{TELEGRAM_API_URL}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response_data = response.json()

        if response.status_code == 200 and response_data.get('ok'):
            return True, response_data
        else:
            print(f"Telegram API error: {response_data}")
            return False, response_data

    except requests.exceptions.RequestException as e:
        print(f"Telegram request failed: {str(e)}")
        return False, {"error": str(e)}


# ==========================================
# GET /notification - Get all notifications
# ==========================================
@app.route("/notification")
def get_all():
    if not db_available:
        return jsonify(
            {
                "code": 503,
                "message": "Database not available. Notifications cannot be retrieved."
            }
        ), 503

    notification_list = db.session.scalars(db.select(Notification)).all()

    if len(notification_list):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "notifications": [n.json() for n in notification_list]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no notifications."
        }
    ), 404


# =====================================================
# GET /notification/<int:notificationID> - Get by ID
# =====================================================
@app.route("/notification/<int:notificationID>")
def find_by_id(notificationID):
    if not db_available:
        return jsonify(
            {
                "code": 503,
                "message": "Database not available. Notification cannot be retrieved."
            }
        ), 503

    notification = db.session.scalar(
        db.select(Notification).filter_by(notificationID=notificationID)
    )

    if notification:
        return jsonify(
            {
                "code": 200,
                "data": notification.json()
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "Notification not found."
        }
    ), 404


# =====================================================
# GET /notification/driver/<int:driverID> - Get by driver
# =====================================================
@app.route("/notification/driver/<int:driverID>")
def find_by_driver(driverID):
    if not db_available:
        return jsonify(
            {
                "code": 503,
                "message": "Database not available. Notifications cannot be retrieved."
            }
        ), 503

    notifications = db.session.scalars(
        db.select(Notification).filter_by(driverID=driverID)
    ).all()

    if len(notifications):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "notifications": [n.json() for n in notifications]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "No notifications found for this driver."
        }
    ), 404


# =====================================================
# POST /notification/send - Send a notification
# =====================================================
# This is the main endpoint that composite services call.
# It logs the notification to the DB and sends it via Telegram.
#
# Expected JSON body:
# {
#     "driverID": 1,          (optional, null for system-wide alerts)
#     "chat_id": "123456789", (Telegram chat ID of the recipient)
#     "message": "Your booking is confirmed!",
#     "type": "booking"       (booking, late-fee, no-show, fault, waitlist)
# }
# =====================================================
@app.route("/notification/send", methods=['POST'])
def send_notification():
    data = request.get_json()

    # Validate required fields
    if not data or 'message' not in data or 'type' not in data:
        return jsonify(
            {
                "code": 400,
                "message": "Missing required fields: 'message' and 'type' are required."
            }
        ), 400

    driver_id = data.get('driverID', None)
    chat_id = data.get('chat_id', None)
    message = data['message']
    notif_type = data['type']

    # Send via Telegram if chat_id is provided
    telegram_status = 'sent'
    if chat_id:
        success, response = send_telegram_message(chat_id, message)
        if not success:
            telegram_status = 'failed'

    # Log to database if available
    notification = None
    if db_available:
        notification = Notification(
            driverID=driver_id,
            message=message,
            type=notif_type,
            status=telegram_status
        )

        try:
            db.session.add(notification)
            db.session.commit()
        except Exception as e:
            return jsonify(
                {
                    "code": 500,
                    "message": f"An error occurred saving the notification: {str(e)}"
                }
            ), 500

    return jsonify(
        {
            "code": 201,
            "data": notification.json() if notification else {"message": message, "type": notif_type, "status": telegram_status},
            "telegram_sent": telegram_status == 'sent'
        }
    ), 201


# =====================================================
# POST /notification/broadcast - Send to multiple drivers
# =====================================================
# Used by the waitlist flow to notify all waitlisted drivers.
#
# Expected JSON body:
# {
#     "drivers": [
#         {"driverID": 1, "chat_id": "111111"},
#         {"driverID": 2, "chat_id": "222222"}
#     ],
#     "message": "A charging slot has opened at [Station]. Book now!",
#     "type": "waitlist"
# }
# =====================================================
@app.route("/notification/broadcast", methods=['POST'])
def broadcast_notification():
    data = request.get_json()

    if not data or 'drivers' not in data or 'message' not in data or 'type' not in data:
        return jsonify(
            {
                "code": 400,
                "message": "Missing required fields: 'drivers', 'message', and 'type' are required."
            }
        ), 400

    drivers = data['drivers']
    message = data['message']
    notif_type = data['type']

    results = []

    for driver in drivers:
        driver_id = driver.get('driverID', None)
        chat_id = driver.get('chat_id', None)

        # Send via Telegram
        telegram_status = 'sent'
        if chat_id:
            success, response = send_telegram_message(chat_id, message)
            if not success:
                telegram_status = 'failed'

        # Log to database if available
        notification = None
        if db_available:
            notification = Notification(
                driverID=driver_id,
                message=message,
                type=notif_type,
                status=telegram_status
            )

            try:
                db.session.add(notification)
                db.session.commit()
                results.append(notification.json())
            except Exception as e:
                db.session.rollback()
                results.append({
                    "driverID": driver_id,
                    "status": "failed",
                    "error": str(e)
                })
        else:
            # No DB, just record the result
            results.append({
                "driverID": driver_id,
                "message": message,
                "type": notif_type,
                "status": telegram_status,
                "telegram_sent": telegram_status == 'sent'
            })

    return jsonify(
        {
            "code": 201,
            "data": {
                "notifications": results
            },
            "message": f"Broadcast sent to {len(drivers)} driver(s)."
        }
    ), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True)
