# Maintenance Microservice

## Overview
The Maintenance microservice handles EV charger maintenance tickets. When a user reports a faulty charger (Scenario 3), a ticket is created. Maintenance staff can update ticket status and mark repairs as complete.

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/maintenance/tickets` | Get all tickets (optional ?status=pending) |
| GET | `/maintenance/ticket/<id>` | Get ticket details with repair logs |
| POST | `/maintenance/ticket` | Create a new maintenance ticket |
| PUT | `/maintenance/ticket/<id>/status` | Update ticket status |
| POST | `/maintenance/repair-complete` | Mark repair as complete |
| GET | `/maintenance/stats` | Get maintenance statistics |

## Usage in Scenario 3 (Faulty Charger)

When a driver reports a faulty charger:
1. Report Fault composite service calls `POST /maintenance/ticket`
2. Maintenance team gets notified via Telegram
3. Team updates status: `PUT /maintenance/ticket/1/status` with status="in_progress"
4. After repair: `POST /maintenance/repair-complete`
5. Notification service sends updates to affected users

## Setup

```bash
pip install -r requirements.txt
python maintenance.py