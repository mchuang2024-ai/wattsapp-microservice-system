# RabbitMQ & Event-Driven Architecture

## Overview

RabbitMQ enables **asynchronous, event-driven communication** between WattsApp microservices. When booking, payment, or charger events occur, they're published as messages that consumers process and forward to appropriate actions (like sending Telegram notifications).

---

## 🏗️ Architecture

```
Microservices (Make_Booking, Handle_NoShow, etc.)
  ↓ publishes events to
RabbitMQ (Topic Exchange: pulsepark.events, wattsapp_topic)
  ↓ routes to
Consumers (notification_amqp.py, error_consumer.py, etc.)
  ↓ process and call
Downstream Services (Notification, Logging, etc.)
```

---

## 📡 Exchanges & Queues

### **Exchange 1: `wattsapp_topic`** (For Notifications)

| Queue | Routing Key | Purpose |
|-------|-------------|---------|
| `notification_queue` | `#` | All messages → Notification service |
| `error_queue` | `*.error` | Error events → Logging/Alerting |
| `activity_log` | `#` | All messages → Activity tracking |

### **Exchange 2: `pulsepark.events`** (For Domain Events)

Suggested routing keys:
- `booking.created` → Create booking notification
- `booking.cancelled` → Cancellation notification
- `late.fee` → Late fee charged notification
- `slot.available` → Waitlist notifications
- `charger.fault` → Maintenance alerts

---

## 🧪 Setup

### **1. Start RabbitMQ**
```bash
docker-compose up -d
```

**Verify:**
- Management UI: `http://localhost:15672` (admin/password123)
- AMQP Port: `localhost:5672`

### **2. Create Exchanges & Queues**
```bash
python amqp_setup.py
```

### **3. Install dependencies**
```bash
pip install -r requirements.txt
```

### **4. Start Consumers**
```bash
python notification_amqp.py
```

---

## 📤 Publishing Events (Code Example)

```python
import pika
import json

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost', port=5672)
)
channel = connection.channel()
channel.exchange_declare(exchange='wattsapp_topic', exchange_type='topic', durable=True)

message = {
    "driverID": 1,
    "chat_id": "1146728523",
    "message": "Your booking is confirmed!",
    "type": "booking"
}

channel.basic_publish(
    exchange='wattsapp_topic',
    routing_key='booking.created',
    body=json.dumps(message),
    properties=pika.BasicProperties(
        content_type='application/json',
        delivery_mode=2  # Persistent
    )
)
connection.close()
```

---

## 🧪 Testing

### **Test Flow:**

**Terminal 1 - Notification Service:**
```bash
cd ../notification && python notification.py
```

**Terminal 2 - AMQP Consumer:**
```bash
python notification_amqp.py
```

**Terminal 3 - Publish Test Message:**
```bash
python test_publish.py
```

**Expected:** Message logged and forwarded to Notification service → **Your Telegram receives it!** ✅

---

## 📊 Message Format Standards

### **Booking Event**
```json
{
  "bookingID": 42,
  "slotID": 101,
  "driverID": 1,
  "station": "Sengkang Hub",
  "chat_id": "1146728523"
}
```

### **Notification Message** (To Notification Service)
```json
{
  "driverID": 1,
  "chat_id": "1146728523",
  "message": "Your booking is confirmed! Slot 101",
  "type": "booking"
}
```

---

## 🔧 Configuration

```bash
AMQP_HOST=localhost          # default
AMQP_PORT=5672               # default
NOTIFICATION_URL=http://localhost:5005/notification/send  # default
RABBITMQ_URL=amqp://admin:password123@localhost:5672/%2F
```

---

## 📚 Full Documentation

- See [../TELEGRAM_INTEGRATION.md](../TELEGRAM_INTEGRATION.md) for complete Telegram setup
- See [amqp_setup.py](amqp_setup.py) for exchange/queue creation code
- See [notification_amqp.py](notification_amqp.py) for consumer implementation