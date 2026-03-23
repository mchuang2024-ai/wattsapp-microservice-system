# Notification Microservice

## Overview
The Notification microservice handles all outbound notifications for the WattsApp EV charging platform. It logs every notification to a MySQL database and sends real-time push messages to drivers via the Telegram Bot API.

## Used In
- **Scenario 1** (Slot Booking): Booking confirmation messages
- **Scenario 2** (No-Show Handling): Grace period warnings, late fee confirmations, no-show cancellations, waitlist broadcasts
- **Scenario 3** (Faulty Charger): Fault reports to maintenance team, cancellation notices to affected drivers, repair completion notices

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notification` | Get all notifications |
| GET | `/notification/<id>` | Get notification by ID |
| GET | `/notification/driver/<driverID>` | Get all notifications for a driver |
| POST | `/notification/send` | Send a single notification |
| POST | `/notification/broadcast` | Send notification to multiple drivers |

### POST /notification/send
```json
{
    "driverID": 1,
    "chat_id": "123456789",
    "message": "Your booking is confirmed!",
    "type": "booking"
}
```
- `driverID`: optional (null for system alerts like fault reports)
- `chat_id`: optional (if omitted, notification is logged to DB only, no Telegram message sent)
- `type`: one of `booking`, `late-fee`, `no-show`, `fault`, `waitlist`

### POST /notification/broadcast
```json
{
    "drivers": [
        {"driverID": 1, "chat_id": "111111"},
        {"driverID": 2, "chat_id": "222222"}
    ],
    "message": "A charging slot has opened!",
    "type": "waitlist"
}
```

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up the database
The database is hosted on Railway. Run `notification_setup.sql` against your Railway MySQL instance to create the table and insert dummy data.

You can connect using:
```
Host: caboose.proxy.rlwy.net
Port: 45033
User: root
Password: jpPOaVCbCXnTWjDOBzPtDoRKYwqqiClR
Database: notification
```

### 3. Get your Telegram chat ID
1. Open Telegram and search for the bot: @WattsAppBot (or whatever you named it)
2. Send `/start` to the bot
3. Open in browser: `https://api.telegram.org/bot8766528831:AAFmXWP5UhrEXaOkvB9VP1ILtnN_oYeUUZc/getUpdates`
4. Find `"chat":{"id": YOUR_NUMBER}` in the response
5. That number is your chat_id for testing

### 4. Run the service
```bash
python notification.py
```
Service runs on port 5005.

### 5. Test
```bash
python test_notification.py
```
Edit `YOUR_CHAT_ID` in the test script to enable Telegram tests.

## Database Schema
```sql
CREATE TABLE Notification (
    notificationID INT AUTO_INCREMENT PRIMARY KEY,
    driverID INT NULL,
    message VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    sentAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(10) NOT NULL DEFAULT 'sent'
        CHECK (status IN ('sent', 'failed'))
);
```

## How Composite Services Call This
The composite services (Handle No-Show, Make Booking, Report Fault) call the Notification service via HTTP POST. Example from Handle No-Show (Scenario 2):

```python
# Inside handle_noshow.py (composite service)
import requests

# Step 7a: Send late fee confirmation
notification_data = {
    "driverID": driver_id,
    "chat_id": driver_chat_id,
    "message": f"You checked in {mins_late} mins late. A late fee of ${fee_amount} has been charged.",
    "type": "late-fee"
}
response = requests.post("http://localhost:5005/notification/send", json=notification_data)
```

## AMQP Integration (RabbitMQ)
The system now includes RabbitMQ for asynchronous messaging. A consumer `rabbitmq/notification_amqp.py` subscribes to events on the `wattsapp_topic` exchange and sends notifications via this service.

### Running the AMQP Consumer
1. Start RabbitMQ: `cd rabbitmq && docker-compose up -d`
2. Set up queues: `python amqp_setup.py`
3. Run consumer: `python notification_amqp.py`

The consumer listens for `late.*`, `slot.*`, `booking.*`, `charger.*`, and `waitlist.*` events and calls the `/notification/send` endpoint. The HTTP endpoints remain available for direct calls.
