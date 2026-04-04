"""
Test script for the Notification microservice.
Run the notification service first: python notification.py
Then run this script: python test_notification.py

This tests all endpoints without needing RabbitMQ or Docker.
"""

import requests
import json

BASE_URL = "http://localhost:5005"

def test_get_all_notifications():
    """Test GET /notification"""
    print("\n=== Test 1: Get all notifications ===")
    response = requests.get(f"{BASE_URL}/notification")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_get_notification_by_id():
    """Test GET /notification/1"""
    print("\n=== Test 2: Get notification by ID ===")
    response = requests.get(f"{BASE_URL}/notification/1")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_get_notifications_by_driver():
    """Test GET /notification/driver/1"""
    print("\n=== Test 3: Get notifications by driver ===")
    response = requests.get(f"{BASE_URL}/notification/driver/1")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_send_notification_no_telegram():
    """Test POST /notification/send without Telegram (no chat_id)"""
    print("\n=== Test 4: Send notification (DB only, no Telegram) ===")
    payload = {
        "driverID": 1,
        "message": "Test notification - no Telegram",
        "type": "booking"
    }
    response = requests.post(f"{BASE_URL}/notification/send", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 201


def test_send_notification_with_telegram(chat_id):
    """Test POST /notification/send with Telegram"""
    print("\n=== Test 5: Send notification (with Telegram) ===")
    payload = {
        "driverID": 1,
        "chat_id": chat_id,
        "message": "🔋 <b>Booking Confirmed!</b>\nSlot 3 at Sengkang Hub is ready for you at 2:00 PM.",
        "type": "booking"
    }
    response = requests.post(f"{BASE_URL}/notification/send", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 201


def test_send_late_fee_notification(chat_id):
    """Test late fee notification matching Scenario 2 Path A"""
    print("\n=== Test 6: Send late fee notification (Scenario 2a) ===")
    payload = {
        "driverID": 2,
        "chat_id": chat_id,
        "message": "⏰ You checked in 6 mins late. A late fee of $3.00 has been charged.",
        "type": "late-fee"
    }
    response = requests.post(f"{BASE_URL}/notification/send", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 201


def test_send_noshow_notification(chat_id):
    """Test no-show notification matching Scenario 2 Path B"""
    print("\n=== Test 7: Send no-show notification (Scenario 2b) ===")
    payload = {
        "driverID": 3,
        "chat_id": chat_id,
        "message": "❌ Your booking at Sengkang Hub has been cancelled due to no-show. Your deposit of $5.00 has been forfeited.",
        "type": "no-show"
    }
    response = requests.post(f"{BASE_URL}/notification/send", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 201


def test_broadcast_waitlist(chat_id):
    """Test broadcast to waitlisted drivers matching Scenario 2 Path B"""
    print("\n=== Test 8: Broadcast waitlist notification ===")
    payload = {
        "drivers": [
            {"driverID": 4, "chat_id": chat_id},
            {"driverID": 5, "chat_id": chat_id}
        ],
        "message": "🅿️ A charging slot has opened at Sengkang Hub. Book now through the app!",
        "type": "waitlist"
    }
    response = requests.post(f"{BASE_URL}/notification/broadcast", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 201


def test_send_fault_notification(chat_id):
    """Test fault notification matching Scenario 3"""
    print("\n=== Test 9: Send fault notification (Scenario 3) ===")
    payload = {
        "driverID": None,
        "chat_id": chat_id,
        "message": "🔧 Fault reported at Slot 3 (Sengkang Hub). Maintenance ticket created.",
        "type": "fault"
    }
    response = requests.post(f"{BASE_URL}/notification/send", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 201


if __name__ == '__main__':
    print("=" * 50)
    print("Notification Microservice Test Suite")
    print("=" * 50)

    # -------------------------------------------------
    # IMPORTANT: To test Telegram, you need your chat ID.
    # 
    # How to get your chat ID:
    # 1. Open Telegram and search for your bot
    # 2. Send any message to the bot (e.g., "/start")
    # 3. Open this URL in your browser:
    #    https://api.telegram.org/bot8766528831:AAFmXWP5UhrEXaOkvB9VP1ILtnN_oYeUUZc/getUpdates
    # 4. Look for "chat":{"id": YOUR_CHAT_ID}
    # 5. Replace the value below with your chat ID
    # -------------------------------------------------
    
    YOUR_CHAT_ID = "483102075"  # Cay's Telegram chat ID

    # Tests that work without Telegram
    test_get_all_notifications()
    test_get_notification_by_id()
    test_get_notifications_by_driver()
    test_send_notification_no_telegram()

    # Tests that require Telegram chat ID
    if YOUR_CHAT_ID:
        test_send_notification_with_telegram(YOUR_CHAT_ID)
        test_send_late_fee_notification(YOUR_CHAT_ID)
        test_send_noshow_notification(YOUR_CHAT_ID)
        test_broadcast_waitlist(YOUR_CHAT_ID)
        test_send_fault_notification(YOUR_CHAT_ID)
    else:
        print("\n⚠️  Skipping Telegram tests - set YOUR_CHAT_ID in this script.")
        print("   See instructions above on how to get your chat ID.")

    print("\n" + "=" * 50)
    print("Tests complete!")
    print("=" * 50)
