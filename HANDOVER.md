# WattsApp / PulsePark — Handover Notes
**IS213 G08-T04 | Branch: `frontend_test`**

---

## 1. Quick Start on a New Computer

### Prerequisites
- **Docker Desktop** (running)
- **Git**

### Clone & Run
```bash
git clone https://github.com/mchuang2024-ai/wattsapp-microservice-system.git
cd wattsapp-microservice-system
git checkout frontend_test
docker-compose up --build
```

First build takes ~5–10 min. All subsequent runs just use `docker-compose up`.

### Set Up RabbitMQ Queues (one-time, after containers are up)
Run this once in a second terminal:
```bash
docker exec -i wattsapp-rabbit python3 << 'EOF'
import pika
conn = pika.BlockingConnection(pika.ConnectionParameters('localhost', credentials=pika.PlainCredentials('admin','password123')))
ch = conn.channel()
ch.exchange_declare(exchange='wattsapp_topic', exchange_type='topic', durable=True)
for q, rk in [('notification_queue','#'), ('error_queue','*.error'), ('activity_log','#')]:
    ch.queue_declare(queue=q, durable=True)
    ch.queue_bind(exchange='wattsapp_topic', queue=q, routing_key=rk)
print('Queues ready')
conn.close()
EOF
```

### Access the App

| Page | URL |
|---|---|
| Dashboard | http://localhost:3000/index.html |
| Find Slots | http://localhost:3000/slots.html |
| My Bookings | http://localhost:3000/bookings.html |
| Report Fault | http://localhost:3000/fault.html |
| RabbitMQ Admin | http://localhost:15673 (admin / password123) |

---

## 2. Service Map

| Service | Port | File |
|---|---|---|
| Driver | 5001 | `driver/` |
| Booking | 5002 | `booking/booking.py` |
| Payment | 5003 | `payment/payment.py` |
| Notification | 5004 | `notification/notification.py` + `notification_amqp.py` |
| Maintenance | 5005 | `maintenance/maintenance.py` |
| View Slots | 5006 | `view_slots/view_slots.py` |
| Report Fault | 5010 | `report_fault/report_fault.py` |
| Make Booking | 5011 | `Make_Booking/app.py` |
| Handle No-Show | 5100 | `handleNoShow/handleNoShow.py` |
| Frontend | 3000 | `frontend/public/` (static HTML) |
| RabbitMQ | 5672 / 15673 | Docker image |

**External services:**
- Telegram Bot: `@ESDWattsAppBot` — Token: `8766528831:AAFmXWP5UhrEXaOkvB9VP1ILtnN_oYeUUZc`
- OutSystems Status API: `https://personal-dftp1xlj.outsystemscloud.com/Status/rest/Status`
- Railway MySQL: `caboose.proxy.rlwy.net:45033` (separate DB per service)

**Telegram Chat IDs:**
- Caylern: `634243561`
- Jin Hong: `483102075`

---

## 3. What Was Built in This Session

### Scenario 2 — Handle No-Show (My Bookings page)

**Files changed:** `booking/booking.py`, `handleNoShow/handleNoShow.py`, `frontend/public/bookings.html`

#### What was added:
- Each confirmed/active booking row now has two new buttons:
  - **Check-in** (cyan) → opens a time picker modal restricted to the slot's start–end window. Shows a live late-fee preview ($0.50/min). If the selected time is after start → calls `handle-noshow` composite with `lateCheckIn=true` + the selected `checkinTime`. If on time → calls booking service directly.
  - **No Show** (red) → confirmation modal showing consequences (deposit forfeited, late count incremented, Telegram sent) → calls `handle-noshow` with `lateCheckIn=false`.

#### Backend changes:
- `handleNoShow.py` — accepts optional `checkinTime` field in request body (format: `"YYYY-MM-DD HH:MM:SS"`). If provided, passes it to the booking check-in endpoint instead of using `datetime.now()`. This allows the UI time picker to drive the late-fee calculation.
- `booking.py` — added `PUT /booking/<id>/noshow` endpoint that sets `status = "no_show"` (separate from cancel). Handle No-Show Path B now calls this instead of `/cancel`, so no-show bookings are distinguishable from regular cancellations in the DB.

#### How to test Scenario 2:
1. Go to **Find Slots** → book a slot (Driver ID: `1`, Charger ID: `1`)
2. Go to **My Bookings** → find the booking
3. **Late Check-in test:** Click **Check-in** → pick a time after the slot start time → confirm → check Telegram for late fee notification
4. **No-show test:** Click **No Show** → confirm → check Telegram for deposit forfeited notification
5. Verify in My Bookings: late check-in shows `late`/`checked-in` status; no-show shows `no_show` status

---

### Scenario 3 — Faulty Charger (Dashboard + Find Slots + My Bookings)

**Files changed:** `booking/booking.py`, `report_fault/report_fault.py`, `frontend/public/index.html`, `frontend/public/slots.html`, `frontend/public/bookings.html`

#### What was added:

**Dashboard (`index.html`):**
- Now fetches `GET /maintenance/tickets` in parallel with view-slots
- Any slot currently in view-slots that has an OPEN maintenance ticket is shown as **Faulty** (red border, "Station Offline" badge, disabled button)
- Stale old tickets (not in current view-slots) are ignored to avoid phantom faulty cards

**Find Slots (`slots.html`):**
- Fetches `GET /maintenance/tickets` before rendering
- Slots with an OPEN maintenance ticket are filtered out entirely — they don't appear in search results

**My Bookings (`bookings.html`):**
- After fault is reported, affected bookings are cancelled in the DB, so refreshing shows them as `cancelled`

#### Backend changes:
- `booking.py` — added `GET /booking/slot/<slotID>` endpoint so report_fault can find all bookings for a faulty slot
- `report_fault.py` step 4 (was broken) — now queries `/booking/slot/<slotID>`, iterates all active bookings for that slot (excluding the reporter), cancels each one via `PUT /booking/<id>/cancel`, and publishes a `charger.fault.affected` AMQP event per affected driver
- `report_fault.py` AMQP events — fixed field names from snake_case (`driver_id`) to camelCase (`driverID`) to match what the notification consumer reads. Added `message` field so Telegram messages actually send.
- `report_fault.py` — added `MAINTENANCE_CHAT_ID` env var (defaults to `634243561`). When a fault is reported, a Telegram alert is sent to the maintenance team via the `charger.fault.reported` AMQP event.

#### How to test Scenario 3:
1. Go to **My Bookings** → click **Report Fault** on an active booking → fill in Slot ID and description → submit
2. **Dashboard** → refresh → the reported station should show red "Faulty / Station Offline" badge
3. **Find Slots** → that slot should no longer appear in results
4. **My Bookings** → other bookings for that slot should show as `cancelled`
5. **Telegram** — three messages should arrive:
   - Maintenance team: fault alert with ticket number
   - Reporting driver: booking cancelled + deposit refunded
   - Other affected drivers: their booking cancelled

---

## 4. Known Issues / Things to Watch

### Payment authorization failed (Book Slot)
If you see "Payment authorization failed" when booking:

```bash
docker-compose logs make-booking --tail=20
docker-compose logs payment --tail=20
```

The error message now shows the exact reason. Common causes:
- Payment container crashed on startup → `docker-compose restart payment`
- Railway MySQL DB connection timeout → retry, it usually recovers

### Dashboard shows 0 Available stations
- Means view-slots can't reach OutSystems or the driver service
- Check: `docker-compose logs view-slots --tail=20`

### Telegram not sending
- Check: `docker-compose logs notification --tail=30`
- RabbitMQ queues might not be set up → re-run the queue setup command from Section 1

### Containers not starting
```bash
docker-compose logs <service-name> --tail=50
docker-compose restart <service-name>
```

---

## 5. Stopping / Resetting

```bash
docker-compose down          # stop containers
docker-compose down -v       # stop + wipe RabbitMQ volume (clean slate)
docker-compose up --build    # rebuild everything from scratch
```

---

## 6. Files Changed Summary (this session)

| File | What changed |
|---|---|
| `booking/booking.py` | Added `GET /booking/slot/<slotID>` and `PUT /booking/<id>/noshow` |
| `handleNoShow/handleNoShow.py` | Accept optional `checkinTime` in request; Path B calls `/noshow` |
| `report_fault/report_fault.py` | Fixed affected booking cancellation; fixed AMQP field names; added maintenance Telegram |
| `frontend/public/bookings.html` | Check-in + No Show buttons with modals; `no_show` status badge |
| `frontend/public/index.html` | Dashboard shows faulty stations from maintenance tickets |
| `frontend/public/slots.html` | Filters out faulty slots from search results |
| `Make_Booking/app.py` | Better error surfacing for payment failures |

**Branch:** `frontend_test`
**Latest commits:**
- `ffa2fd4` — fix: dashboard stale faulty cards and payment error surfacing
- `fe0a538` — feat: scenario 2 check-in/no-show UI, scenario 3 fault cascade fixes
