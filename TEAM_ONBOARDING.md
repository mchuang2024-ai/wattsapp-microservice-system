# 🚗 WattsApp Microservice System - Team Overview

## Welcome to WattsApp! 👋

This is a **microservice-based EV charging platform** that handles booking, payments, notifications, and charger management via Telegram.

---

## 📋 System Components

```
┌─────────────────────────────────────────────────────────┐
│                    WATTSAPP SERVICES                     │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  01. Make_Booking (Port 5001)    🎫 Orchestrates        │
│  ├─→ Calls Payment Service (5002)                       │
│  ├─→ Calls Booking Service (5003)                       │
│  └─→ Publishes to RabbitMQ                              │
│                                                           │
│  02. Notification (Port 5005)    📱 Sends Telegram       │
│  ├─→ Receives HTTP requests                             │
│  ├─→ Sends to Telegram Bot API                          │
│  └─→ Logs to MySQL database                             │
│                                                           │
│  03. Status (Port 5006)          ⚡ Charger States       │
│  ├─→ Tracks slot availability                           │
│  ├─→ available, occupied, faulty                        │
│  └─→ MySQL database                                     │
│                                                           │
│  04. RabbitMQ (Port 5672)        🐰 Event Bus            │
│  ├─→ Exchanges: wattsapp_topic, pulsepark.events        │
│  ├─→ Consumers: notification_amqp.py                    │
│  └─→ Management UI: 15672                               │
│                                                           │
│  05. Payment (Port 5002)         💳 Payment Hold/Release │
│  06. Booking (Port 5003)         📅 Slot Reservation    │
│  07. Driver (Port 5004)          👤 Driver Profiles     │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 Complete Booking Flow

```
1. User calls /create-booking (Make_Booking on 5001)
   ↓
2. Service validates JSON
   ↓
3. Calls Payment Service → Holds $5 deposit
   ❌ If fails: Return "Payment failed"
   ✅ If success: Continue
   ↓
4. Calls Booking Service → Creates booking record
   ❌ If fails: Release payment (rollback) → Return "Booking failed"
   ✅ If success: Get bookingID
   ↓
5. Publishes event to RabbitMQ
   {
     "bookingID": 42,
     "slotID": 101,
     "driverID": 1,
     "chat_id": "1146728523",  ← CRITICAL
     "station": "Sengkang Hub"
   }
   ↓
6. notification_amqp.py consumer receives it
   ↓
7. Forwards to Notification Service (/notification/send)
   ↓
8. Notification Service calls Telegram Bot API
   ↓
9. 🎉 Driver gets Telegram message!
```

---

## 📱 Telegram Integration

### **Current Bot**
- **Bot Token:** `8761333590:AAGGqcM1cETwjMQRpoVpr5OIEEOJ2vMtraQ`
- **My Chat ID:** `1146728523` (For testing)
- **Bot Username:** `@WattsAppBot`

### **How Messages Work**

1. **Chat ID** is like a mailing address
   - Each driver needs their own Chat ID
   - Store in database: `Driver.telegram_chat_id`

2. **When booking happens:**
   - Message includes `chat_id`: `1146728523`
   - Telegram Bot API receives it
   - Message appears on driver's phone

3. **Supported notification types:**
   - `booking` - Booking confirmed
   - `late-fee` - Late checkout charged
   - `no-show` - Booking cancelled
   - `fault` - Charger broken
   - `waitlist` - Slot available

---

## 🛠️ Your Tech Stack

### **Languages & Frameworks**
- **Python 3.8+** - All microservices
- **Flask** - REST APIs
- **SQLAlchemy** - ORM for databases

### **Databases**
- **MySQL** - Persistent data (notifications, bookings, drivers)
- **RabbitMQ** - Message broker (events)

### **Key Libraries**
- `flask` - Web framework
- `flask_cors` - Cross-origin requests
- `requests` - HTTP client
- `pika` - RabbitMQ client
- `sqlalchemy` - Database ORM
- `mysql-connector-python` - MySQL driver

### **Infrastructure**
- **Docker** - Containerization
- **docker-compose** - Multi-container orchestration
- **Railway** - Cloud MySQL hosting (optional)

---

## 📂 Folder Structure

```
wattsapp-microservice-system/
├── Make_Booking/
│   ├── app.py             ← Booking orchestration
│   ├── config.py          ← Environment config
│   ├── models.py          ← Database models
│   ├── requirements.txt    ← Dependencies
│   └── README.md           ← How Make_Booking works
│
├── notification/
│   ├── notification.py    ← Notification API
│   ├── notification_setup.sql
│   ├── requirements.txt
│   ├── test_notification.py
│   └── README.md
│
├── status/
│   ├── status.py          ← Charger status API
│   ├── status_setup.sql
│   ├── requirements.txt
│   └── README.md
│
├── rabbitmq/
│   ├── amqp_setup.py      ← Create exchanges/queues
│   ├── notification_amqp.py  ← Consumer (listens for messages)
│   ├── test_publish.py    ← Test message publishing
│   ├── compose.yaml       ← Docker Compose for RabbitMQ
│   ├── requirements.txt
│   └── README.md
│
├── payment.py             ← Payment service (stub)
├── driver/                ← Driver service (stub)
│
├── TELEGRAM_INTEGRATION.md   ← Full Telegram guide
├── QUICK_REFERENCE.md       ← 5-minute cheat sheet
└── README.md               ← Project overview
```

---

## 🚀 First Time Setup

### **1. Clone & Install**
```bash
git clone <repo>
cd wattsapp-microservice-system
pip install -r notification/requirements.txt
pip install -r status/requirements.txt
pip install -r rabbitmq/requirements.txt
```

### **2. Start Docker Infrastructure**
```bash
cd rabbitmq
docker-compose up -d
python amqp_setup.py  # Create exchanges/queues
```

### **3. Run Services (in separate terminals)**
```bash
# Terminal 1
cd notification && python notification.py

# Terminal 2
cd rabbitmq && python notification_amqp.py

# Terminal 3
cd Make_Booking && python app.py

# Terminal 4
cd status && python status.py
```

### **4. Test Booking Flow**
```bash
curl -X POST http://localhost:5001/create-booking \
  -H "Content-Type: application/json" \
  -d '{
    "driverID": 1,
    "chargerID": 101,
    "starttime": "2026-04-01T14:00:00",
    "endtime": "2026-04-01T15:00:00",
    "deposit": 5.0
  }'
```

---

## 🧪 Testing Services Individually

### **Notification Service**
```bash
curl -X POST http://localhost:5005/notification/send \
  -H "Content-Type: application/json" \
  -d '{
    "driverID": 1,
    "chat_id": "1146728523",
    "message": "Test!",
    "type": "test"
  }'
```

### **Status Service**
```bash
# Get all statuses
curl http://localhost:5006/status

# Get by state
curl http://localhost:5006/status/state/available

# Create new
curl -X POST http://localhost:5006/status \
  -H "Content-Type: application/json" \
  -d '{"status": "occupied"}'
```

### **RabbitMQ Management UI**
- Visit: `http://localhost:15672`
- Login: `admin` / `password123`
- View queues, exchanges, connections

---

## 📊 Common Development Tasks

### **Add a New Endpoint**
```python
# In notification.py or Make_Booking/app.py
@app.route('/new-endpoint', methods=['POST'])
def my_endpoint():
    data = request.get_json()
    # Your logic
    return jsonify({"result": "success"}), 200
```

### **Send Telegram from Your Code**
```python
import requests

requests.post('http://localhost:5005/notification/send', json={
    "driverID": 1,
    "chat_id": "1146728523",
    "message": "Your message here",
    "type": "booking"
})
```

### **Publish RabbitMQ Event**
```python
import pika, json

conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
ch = conn.channel()
ch.exchange_declare(exchange='wattsapp_topic', exchange_type='topic', durable=True)
ch.basic_publish(
    exchange='wattsapp_topic',
    routing_key='your.event',
    body=json.dumps({"key": "value"})
)
conn.close()
```

### **Query Notifications from DB**
```bash
mysql -h caboose.proxy.rlwy.net -P 45033 -u root -p
# Password: jpPOaVCbCXnTWjDOBzPtDoRKYwqqiClR

USE notification;
SELECT * FROM Notification WHERE driverID = 1 ORDER BY sentAt DESC LIMIT 10;
```

---

## 🐛 Debugging Checklist

**Service not starting?**
- Check port isn't in use: `lsof -i :5001` (Mac/Linux)
- Check dependencies: `pip install -r requirements.txt`
- Look at error message carefully

**RabbitMQ not connecting?**
- Run `docker-compose up -d` again
- Check `docker ps` shows rabbitmq container
- Verify credentials: `admin` / `password123`

**Telegram message not received?**
- Verify Chat ID: `1146728523`
- Check consumer running: `python notification_amqp.py`
- Check notification service running: `python notification.py`
- Check logs for errors

**Messages piling up in RabbitMQ?**
- Check consumer isn't crashed
- Look at notification service logs
- Check message format is valid JSON

---

## 📞 Need Help?

- **Documentation:** See `README.md` files in each folder
- **Quick Start:** `QUICK_REFERENCE.md`
- **Telegram Guide:** `TELEGRAM_INTEGRATION.md`
- **RabbitMQ Help:** `rabbitmq/README.md`
- **Logs:** Check terminal output of each service

---

## 🎯 Current Status

✅ **Implemented:**
- Make_Booking orchestration service
- Notification microservice with Telegram integration
- Status charger service
- RabbitMQ event infrastructure
- AMQP consumer for notifications
- Comprehensive documentation

🔄 **In Progress:**
- Payment service mock/real implementation
- Booking service implementation
- Driver service implementation
- Additional consumers (error handling, logging)

📋 **TODO:**
- Production deployment (Kubernetes/Docker Swarm)
- Monitoring & alerting (Prometheus)
- Load testing
- Integration tests

---

## 🚀 Ready to Code!

1. Pick a service to work on
2. Read its `README.md`
3. Look at `QUICK_REFERENCE.md` for common patterns
4. Start coding!
5. Test with the provided endpoints

**Let's build WattsApp together! 🎉**
