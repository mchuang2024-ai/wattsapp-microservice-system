# Make Booking Service

## Overview

The Make Booking Service is a **composite microservice** that orchestrates the EV charging slot booking workflow. It coordinates multiple downstream services and publishes events to trigger notifications.

---

## 🎯 Endpoint

### `POST /create-booking`

**Request:**
```json
{
  "driverID": 1,
  "chargerID": 101,
  "starttime": "2026-04-01T14:00:00",
  "endtime": "2026-04-01T15:00:00",
  "deposit": 5.0
}
```

**Response (Success):**
```json
{
  "status": "confirmed",
  "bookingID": 42,
  "message": "Slot reserved successfully"
}
```

**Response (Error):**
```json
{
  "error": "Payment authorization failed",
  "details": "..."
}
```

---

## 🔄 Orchestration Flow (Exact Sequence)

### **Step 1: Validate Request**
- Check JSON format
- Verify required fields: `driverID`, `chargerID`, `starttime`, `endtime`, `deposit`
- Return 400 if invalid

### **Step 2: Call Payment Service**
- **Endpoint:** `POST http://payment:5002/payment/hold`
- **Payload:** `{ "driverID": driverID, "deposit": deposit }`
- **Status:** Must return 200
- **On Failure:** Return error immediately, no rollback needed yet

### **Step 3: Call Booking Service**
- **Endpoint:** `POST http://booking:5003/bookings`
- **Payload:** `{ "driverID", "chargerID", "starttime", "endtime" }`
- **Status:** Must return 200 or 201
- **Extract:** `bookingID` from response
- **On Failure:** 
  - Call `POST http://payment:5002/payment/release` (rollback)
  - Return error

### **Step 4: Publish RabbitMQ Event**
- **Exchange:** `pulsepark.events`
- **Routing Key:** `booking.created`
- **Message:**
  ```json
  {
    "bookingID": 42,
    "slotID": 101,
    "driverID": 1,
    "station": "Sengkang Hub"
  }
  ```
- **Note:** If fails, continue (don't rollback booking)

### **Step 5: Optional DB Logging**
- Log booking to `booking_logs` table (if MySQL available)
- Non-critical - errors don't affect response

### **Step 6: Return Success**
```json
{
  "status": "confirmed",
  "bookingID": 42,
  "message": "Slot reserved successfully"
}
```

---

## 📱 Telegram Notifications

When booking is confirmed, the `booking.created` event triggers:

1. **RabbitMQ Consumer** (`rabbitmq/notification_amqp.py`) receives event
2. **Consumer** calls Notification Service with message
3. **Notification Service** sends Telegram message to driver

**For notifications to work:**
- Driver's Chat ID must be included in booking event:
  ```json
  {
    "bookingID": 42,
    "slotID": 101,
    "driverID": 1,
    "station": "Sengkang Hub",
    "chat_id": "1146728523"  // ADD THIS
  }
  ```

Or pass it separately to the consumer. See [TELEGRAM_INTEGRATION.md](../TELEGRAM_INTEGRATION.md) for full setup.

---

## 🐍 File Structure

```
Make_Booking/
├── app.py          # Main Flask app with /create-booking endpoint
├── config.py       # Configuration (URLs, database, RabbitMQ)
├── models.py       # BookingLog database model (optional)
└── requirements.txt  # Python dependencies
```

---

## 🚀 Running Locally

### **Prerequisites:**
- Python 3.8+
- Dependencies: `flask`, `flask_cors`, `requests`, `pika`, `flask_sqlalchemy`

### **Steps:**

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start payment & booking services** (mocks or real):
   - Payment on `http://localhost:5002`
   - Booking on `http://localhost:5003`

3. **Start RabbitMQ:**
   ```bash
   cd ../rabbitmq
   docker-compose up -d
   ```

4. **Run Make Booking service:**
   ```bash
   python app.py
   ```
   Service runs on port **5001**

---

## 🧪 Testing

### **Test 1: Happy Path (All Services Available)**
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

**Expected Response:**
```json
{
  "status": "confirmed",
  "bookingID": 123,
  "message": "Slot reserved successfully"
}
```

### **Test 2: Payment Service Fails**
- Stop payment service on port 5002
- Send same request
- **Expected:** `{"error": "Payment authorization failed", "details": "..."}`

### **Test 3: Booking Service Fails (After Payment)**
- Payment returns 200
- Booking returns 500
- **Expected:** 
  - Booking fails
  - Payment release is called
  - Response: `{"error": "Booking creation failed"}`
  - No booking created in database

---

## 🔌 Environment Variables

```bash
PAYMENT_URL=http://payment:5002/payment/hold      # Default
BOOKING_URL=http://booking:5003/bookings         # Default
RABBITMQ_URL=amqp://admin:password123@localhost:5672/%2F
SQLALCHEMY_DATABASE_URI=mysql+mysqlconnector://root:rootpass@localhost:3306/pulsepark
```

Override in Docker:
```yaml
services:
  make-booking:
    environment:
      - PAYMENT_URL=http://payment:5002/payment/hold
      - BOOKING_URL=http://booking:5003/bookings
      - RABBITMQ_URL=amqp://admin:password123@rabbitmq:5672/%2F
```

---

## 📊 Error Codes

| Code | Scenario | Action |
|------|----------|--------|
| 200 | Booking confirmed | ✅ Event published, response sent |
| 400 | Invalid JSON/fields | ❌ Validation failed, no calls made |
| 500 | Payment/Booking/RabbitMQ fails | ❌ Rollback payment if needed |

---

## 🔄 Deployment (Docker)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

**docker-compose snippet:**
```yaml
services:
  make-booking:
    build:
      context: ./Make_Booking
    container_name: make-booking
    environment:
      - PAYMENT_URL=http://payment:5002/payment/hold
      - BOOKING_URL=http://booking:5003/bookings
      - RABBITMQ_URL=amqp://admin:password123@rabbitmq:5672/%2F
    ports:
      - "5001:5001"
    depends_on:
      - payment
      - booking
      - rabbitmq
```

---

## 📚 Related Documentation

- [TELEGRAM_INTEGRATION.md](../TELEGRAM_INTEGRATION.md) - How notifications work
- [rabbitmq/README.md](../rabbitmq/README.md) - Event publishing
- [notification/README.md](../notification/README.md) - Notification service API
