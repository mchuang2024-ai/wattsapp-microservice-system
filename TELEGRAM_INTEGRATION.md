# WattsApp Telegram Integration Guide

## Overview

Your WattsApp system sends real-time notifications to drivers via **Telegram Bot API**. This guide explains how the integration works and how to use it.

---

## 🔑 Current Credentials

| Component | Value | Purpose |
|-----------|-------|---------|
| **Bot Token** | `8761333590:AAGGqcM1cETwjMQRpoVpr5OIEEOJ2vMtraQ` | Authenticates requests to Telegram Bot API |
| **Chat ID** | `1146728523` | Your personal chat ID for testing |
| **Bot Username** | `@WattsAppBot` | Find bot on Telegram |

---

## 🏗️ Architecture Flow

```
Event Triggered
  ↓
Make_Booking / Composite Service publishes event
  ↓
RabbitMQ (pulsepark.events or wattsapp_topic)
  ↓
notification_amqp.py Consumer receives message
  ↓
Calls Notification Service (http://localhost:5005/notification/send)
  ↓
Notification Service sends to Telegram Bot API
  ↓
Telegram Bot delivers message to driver's phone
✅ Driver receives notification
```

---

## 📱 How Notifications Work

### **1. Publishing an Event (in your service)**

```python
import requests
import json

# From Make_Booking, payment, or any microservice:
notification_payload = {
    "driverID": 1,
    "chat_id": "1146728523",  # Driver's Telegram Chat ID
    "message": "Your EV slot booking is confirmed! Slot 101, Sengkang Hub",
    "type": "booking"  # Types: booking, late-fee, no-show, fault, waitlist
}

# Direct HTTP call:
requests.post(
    'http://localhost:5005/notification/send',
    json=notification_payload
)

# OR publish to RabbitMQ (recommended for async):
import pika
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.basic_publish(
    exchange='pulsepark.events',
    routing_key='booking.created',
    body=json.dumps(notification_payload)
)
```

### **2. Consumer Processes It (rabbitmq/notification_amqp.py)**

The consumer runs continuously:
```bash
cd rabbitmq
python notification_amqp.py
```

It:
- Listens to `wattsapp_topic` exchange
- Receives messages with routing keys: `booking.*`, `late.*`, `slot.*`, etc
- Forwards to Notification service
- Logs success/failure

### **3. Notification Service Sends to Telegram**

The service forwards to Telegram Bot API:
```python
url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
requests.post(url, json={
    'chat_id': '1146728523',
    'text': 'Your EV slot booking is confirmed!',
    'parse_mode': 'HTML'
})
```

### **4. Driver Receives on Phone**

✅ Message appears in Telegram chat

---

## 🧪 Testing End-to-End

### **Prerequisites:**
- Telegram bot created (`@WattsAppBot`)
- You've sent `/start` to the bot
- Chat ID extracted: `1146728523`
- Services running

### **Test Steps:**

**Terminal 1: Start Notification Service**
```bash
cd notification
python notification.py
```

**Terminal 2: Start AMQP Consumer**
```bash
cd rabbitmq
python notification_amqp.py
```

**Terminal 3: Publish Test Message**
```bash
cd rabbitmq
python test_publish.py
```

**Expected Output:**
- Terminal 2 logs: `"Received message with routing key..."`
- Terminal 2 logs: `"Notification sent successfully"`
- **Your Telegram receives: "Test notification from RabbitMQ!"** ✅

---

## 📝 Notification Types

### **Booking Confirmation**
```json
{
  "driverID": 1,
  "chat_id": "1146728523",
  "message": "✅ Booking confirmed! Slot 101 reserved from 14:00-15:00",
  "type": "booking"
}
```

### **Late Fee**
```json
{
  "driverID": 1,
  "chat_id": "1146728523",
  "message": "⏰ You checked out 15 mins late. Late fee: $5 charged.",
  "type": "late-fee"
}
```

### **Fault Alert**
```json
{
  "driverID": null,
  "chat_id": "1146728523",
  "message": "⚠️ Charger 101 is faulty. Avoiding bookings.",
  "type": "fault"
}
```

### **Waitlist Notification**
```json
{
  "driverID": 1,
  "chat_id": "1146728523",
  "message": "🎉 A slot opened at Sengkang Hub! Book now!",
  "type": "waitlist"
}
```

---

## 🔧 Configuration for Multiple Drivers

Each driver has their own **Chat ID**. To find a driver's Chat ID:

1. **Driver creates their bot account** (or use shared bot)
2. **Driver messages the bot** with `/start`
3. **Admin extracts Chat ID** via:
   ```
   https://api.telegram.org/bot8761333590:AAGGqcM1cETwjMQRpoVpr5OIEEOJ2vMtraQ/getUpdates
   ```
4. **Store Chat ID in Driver database:**
   ```sql
   ALTER TABLE Driver ADD COLUMN telegram_chat_id VARCHAR(100);
   UPDATE Driver SET telegram_chat_id = '1146728523' WHERE driverID = 1;
   ```
5. **Pass Chat ID in notification payload:**
   ```python
   driver = get_driver(driver_id)
   notification = {
       "driverID": driver_id,
       "chat_id": driver.telegram_chat_id,
       "message": "Your booking is ready!",
       "type": "booking"
   }
   requests.post('http://localhost:5005/notification/send', json=notification)
   ```

---

## 🔐 Environment Variables

Set these in your `.env` or deployment config:

```bash
TELEGRAM_BOT_TOKEN=8761333590:AAGGqcM1cETwjMQRpoVpr5OIEEOJ2vMtraQ
RABBITMQ_URL=amqp://admin:password123@localhost:5672/%2F
NOTIFICATION_URL=http://localhost:5005/notification/send
```

To override defaults:
```bash
export TELEGRAM_BOT_TOKEN=your_token_here
python notification.py
```

---

## 📊 Database Logging

All notifications are logged to `notification` database:

```sql
SELECT * FROM Notification WHERE driverID = 1 ORDER BY sentAt DESC;
```

Columns:
- `notificationID` - Unique ID
- `driverID` - Driver who received it
- `message` - Notification text
- `type` - booking, late-fee, no-show, fault, waitlist
- `sentAt` - Timestamp
- `status` - sent or failed

---

## ❌ Troubleshooting

### **Issue: "Telegram API error: 400 Bad Request"**
- ✅ Chat ID is invalid or expired
- **Fix:** Verify Chat ID in `getUpdates` response

### **Issue: "Failed to resolve 'localhost'"**
- ✅ Running in Docker/network isolation
- **Fix:** Update `NOTIFICATION_URL` to service hostname, e.g., `http://notification:5005/notification/send`

### **Issue: Consumer not receiving messages**
- ✅ RabbitMQ not running or exchange not created
- **Fix:** Run `python amqp_setup.py` to create exchanges/queues

### **Issue: Telegram message not received**
- ✅ Bot token expired or Chat ID wrong
- **Fix:** 
  1. Verify token in `notification.py`
  2. Check Chat ID via `/getUpdates`
  3. Ensure you sent `/start` to bot

---

## 🚀 Next Steps for Your Team

1. **Each developer gets a Chat ID:**
   - Message `@WattsAppBot`
   - Extract ID from `/getUpdates`
   - Update local `test_publish.py`

2. **Add Chat ID to Driver model:**
   - Database column: `telegram_chat_id`
   - Collect from drivers during onboarding

3. **Deploy consumers in production:**
   - (Optional) Use systemd/docker to auto-restart consumers
   - Monitor consumer logs for failures

4. **Set up alerts:**
   - Monitor `status: failed` in Notification table
   - Alert on RabbitMQ queue backlog

---

## 📚 Related Files

- [notification/README.md](../../notification/README.md) - Notification service API
- [rabbitmq/README.md](../../rabbitmq/README.md) - RabbitMQ setup
- [Make_Booking/app.py](../../Make_Booking/app.py) - Booking orchestration
- [rabbitmq/notification_amqp.py](../notification_amqp.py) - Consumer logic
