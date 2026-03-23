# RabbitMQ Setup for WattsApp Microservices

This folder contains the RabbitMQ configuration and AMQP consumers for the WattsApp EV charging platform.

## Overview

RabbitMQ is used for asynchronous messaging between microservices. The system uses a topic exchange `wattsapp_topic` to route messages based on routing keys.

## Setup

### 1. Start RabbitMQ
```bash
docker-compose up -d
```
This starts RabbitMQ with management UI at http://localhost:15672 (admin/password123).

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up exchanges and queues
```bash
python amqp_setup.py
```
This creates the `wattsapp_topic` exchange and binds queues.

### 4. Run consumers
```bash
python notification_amqp.py
```
This starts the notification consumer that listens for events and sends notifications.

## Architecture

- **Exchange**: `wattsapp_topic` (topic type)
- **Queues**:
  - `notification_queue`: Binds to `#` (all messages)
  - `error_queue`: Binds to `*.error`
  - `activity_log`: Binds to `#`

## Message Format

Messages are JSON objects sent to the notification service:

```json
{
    "driverID": 1,
    "chat_id": "123456789",
    "message": "Your booking is confirmed!",
    "type": "booking"
}
```

## Routing Keys

- `late.*`: Late fee notifications
- `slot.*`: Slot status updates
- `booking.*`: Booking confirmations
- `charger.*`: Charger fault reports

## Environment Variables

- `AMQP_HOST`: RabbitMQ host (default: localhost)
- `AMQP_PORT`: RabbitMQ port (default: 5672)
- `NOTIFICATION_URL`: Notification service URL (default: http://localhost:5005/notification/send)