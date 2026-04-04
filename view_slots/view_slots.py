from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import requests
import config

app = Flask(__name__)
CORS(app)
#check drivers late count score. if 5 and above, return no slots available or some message banned
#check status on outsystems, get list of available charger slotid
#check the date, get all 1 hour slots on that date as well as the charger slotid its associated with
#check booking service, if any slots booked for that date and hour, remove those time slots
#return all available time slots for that date 

@app.route('/view-slots', methods=['GET'])
def view_slots():
    """
    GET /view-slots?date=2024-03-23&driverID=123
    """
    date = request.args.get('date')
    driver_id = request.args.get('driverID')
    if not date or not driver_id:
        return jsonify({'error': 'Missing required parameters: date, driverID'}), 400
    
    try:
        with ThreadPoolExecutor(max_workers=3) as executor:
            driver_future = executor.submit(requests.get, f'{config.DRIVER_URL}/drivers/{driver_id}', timeout=5)
            outsystems_future = executor.submit(requests.get, f'{config.OUTSYSTEMS_BASE_URL}/available', timeout=10)
            booking_future = executor.submit(requests.get, f'{config.BOOKING_URL}/booking/date/{date}', timeout=5)
            
            driver_response = driver_future.result()
            outsystems_response = outsystems_future.result()
            booking_response = booking_future.result()
        
        if driver_response.status_code != 200:
            return jsonify({'error': 'Driver not found'}), 404
        
        driver_data = driver_response.json()
        if driver_data.get('data', {}).get('late_count', 0) >= 5:
            return jsonify({'error': 'Too many late arrivals, please contact support'}), 403
        
        if outsystems_response.status_code != 200:
            return jsonify({'error': 'Failed to fetch available slots from OutSystems'}), 500
        
        available_slots = outsystems_response.json()
        available_slot_ids = [slot['slotID'] for slot in available_slots]
        
        booked_slots = []
        if booking_response.status_code == 200:
            bookings = booking_response.json().get('data', {}).get('bookings', [])
            for booking in bookings:
                start_time = datetime.strptime(booking['startTime'], '%Y-%m-%d %H:%M:%S')
                booked_slots.append((booking['slotID'], start_time.hour))                

        all_time_slots = []
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        for slot_id in available_slot_ids:
            for hour in range(24):
                start_time = datetime.combine(target_date, datetime.min.time()).replace(hour=hour)
                end_time = start_time + timedelta(hours=1)
                
                if (slot_id, hour) not in booked_slots:
                    all_time_slots.append({
                        'date': date,
                        'slotID': slot_id,
                        'startTime': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'endTime': end_time.strftime('%Y-%m-%d %H:%M:%S')
                    })
        
        return jsonify({
            'totalSlots': len(all_time_slots),
            'slots': all_time_slots
        }), 200


    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Service communication error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5006, debug=True)

