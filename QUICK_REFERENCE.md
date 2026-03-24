# ⚡ Quick Reference - WattsApp Telegram Integration

## 🔑 Your Credentials

```
Bot Token:  8761333590:AAGGqcM1cETwjMQRpoVpr5OIEEOJ2vMtraQ
Chat ID:    1146728523
Bot Name:   @WattsAppBot
```

---

## 🚀 Quick Start (5 minutes)

### **1. Start Everything (New Terminal Tabs)**

```bash
# Terminal 1: RabbitMQ
cd rabbitmq
docker-compose up -d

# Terminal 2: Notification Service
cd notification
python notification.py

# Terminal 3: AMQP Consumer
cd rabbitmq
python notification_amqp.py

# Terminal 4: Test
cd rabbitmq
python test_publish.py
```

### **2. Check Your Telegram**
Look for message: "Test notification from RabbitMQ!" ✅

---

## 📱 Send a Notification Programmatically

### **Method 1: Direct HTTP (Sync)**
```python
import requests

requests.post('http://localhost:5005/notification/send', json={
    "driverID": 1,
    "chat_id": "1146728523",
    "message": "🎉 Your booking is confirmed!",
    "type": "booking"
})
```

### **Method 2: RabbitMQ (Async)**
```python
import pika, json

conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
ch = conn.channel()
ch.exchange_declare(exchange='wattsapp_topic', exchange_type='topic', durable=True)
ch.basic_publish(
    exchange='wattsapp_topic',
    routing_key='booking.created',
    body=json.dumps({
        "driverID": 1,
        "chat_id": "1146728523",
        "message": "🎉 Your booking is confirmed!",
        "type": "booking"
    })
)
conn.close()
```

---

## 🔐 Environment Setup

Copy to `.env`:
```
TELEGRAM_BOT_TOKEN=8761333590:AAGGqcM1cETwjMQRpoVpr5OIEEOJ2vMtraQ
TELEGRAM_CHAT_ID=1146728523
RABBIT_HOST=localhost
RABBIT_PORT=5672
```

Use in code:
```python
import os
token = os.getenv('TELEGRAM_BOT_TOKEN', '8761333590:...')
```

---

## 📝 Notification Types

| Type | Example Message |
|------|-----------------|
| `booking` | "✅ Booking confirmed! Slot 101, Sengkang Hub" |
| `late-fee` | "⏰ Late fee $5 charged" |
| `no-show` | "⚠️ Booking cancelled (no-show)" |
| `fault` | "🔧 Charger maintenance - avoiding bookings" |
| `waitlist` | "🎉 Slot opened! Book now!" |

---

## 🧪 Common Tests

### **Test 1: Direct Notification**
```bash
curl -X POST http://localhost:5005/notification/send \
  -H "Content-Type: application/json" \
  -d '{
    "driverID": 1,
    "chat_id": "1146728523",
    "message": "Test from curl!",
    "type": "test"
  }'
```

### **Test 2: RabbitMQ Direct Publish**
```bash
python -c "
import pika, json
ch = pika.BlockingConnection(pika.ConnectionParameters()).channel()
ch.exchange_declare(exchange='wattsapp_topic', exchange_type='topic', durable=True)
ch.basic_publish(exchange='wattsapp_topic', routing_key='test.msg', body=json.dumps({
    'driverID': 1, 'chat_id': '1146728523', 'message': 'RabbitMQ test!', 'type': 'test'
}))
print('Published!')
"
```

### **Test 3: Verify in Management UI**
Visit: `http://localhost:15672`
- Username: `admin`
- Password: `password123`
- Look for: `wattsapp_topic` exchange, `notification_queue` with messages

---

## ❌ Troubleshooting Checklist

| Problem | Check | Fix |
|---------|-------|-----|
| No Telegram message | Is consumer running? | `python notification_amqp.py` |
| "Failed to resolve payment" | Payment service running? | Start payment service on 5002 |
| Empty queue | Message published? | Check routing keys match |
| "Invalid Chat ID" | Did you use real ID? | Use `1146728523` for testing |
| Connection refused | RabbitMQ running? | `docker-compose up -d` |

---

## 📚 Full Docs

- **Telegram Setup**: [TELEGRAM_INTEGRATION.md](../TELEGRAM_INTEGRATION.md)
- **RabbitMQ**: [rabbitmq/README.md](README.md)
- **Make Booking**: [Make_Booking/README.md](../Make_Booking/README.md)
- **Notification Service**: [notification/README.md](../notification/README.md)

---

## 🎯 For Your Team

### **Finding Your Own Chat ID**

1. Visit: `https://api.telegram.org/bot8761333590:AAGGqcM1cETwjMQRpoVpr5OIEEOJ2vMtraQ/getUpdates`
2. Look for: `"id": YOUR_NUMBER_HERE`
3. Use that in notifications

### **Adding a Driver to DB**

```sql
UPDATE Driver SET telegram_chat_id = '1146728523' WHERE driverID = 1;
```

### **Sending Bulk Notifications**

```python
drivers = [
    {"driverID": 1, "chat_id": "1146728523"},
    {"driverID": 2, "chat_id": "9876543210"},
]

requests.post('http://localhost:5005/notification/broadcast', json={
    "drivers": drivers,
    "message": "🎉 Special promotion: $2 off all bookings!",
    "type": "promo"
})
```

---

## 🚢 Production Deployment

Use Docker Compose:
```bash
docker-compose -f ../rabbitmq/compose.yaml up -d

# Or individual services:
docker build -t notification:latest notification/
docker build -t make-booking:latest Make_Booking/
docker build -t rabbitmq-consumer:latest rabbitmq/
```

---

## 📊 Live Monitoring

**Queue depth:**
```bash
python -c "
import pika
ch = pika.BlockingConnection(pika.ConnectionParameters()).channel()
method = ch.queue_declare(queue='notification_queue', passive=True)
print(f'Messages in queue: {method.method.message_count}')
"
```

**Telegram bot stats:**
```
GET https://api.telegram.org/bot8761333590:AAGGqcM1cETwjMQRpoVpr5OIEEOJ2vMtraQ/getMe
```

---

## 💡 Tips

- ✅ Always include `chat_id` in notifications
- ✅ Use durable queues: `channel.queue_declare(durable=True)`
- ✅ Log errors: `print(f"Error: {e}")`
- ✅ Test with your own Chat ID first: `1146728523`
- ✅ Watch consumer logs during testing

**Happy notifying! 🚀**
