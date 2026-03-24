from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)

# DATABASE CONFIG (Railway)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL',
    'mysql+mysqlconnector://root:jpPOaVCbCXnTWjDOBzPtDoRKYwqqiClR@caboose.proxy.rlwy.net:45033/notification')
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)
CORS(app)

# MODEL
class ChargingSlot(db.Model):
    __tablename__ = 'ChargingSlot'
    
    slotID = db.Column(db.String(50), primary_key=True)
    stationID = db.Column(db.String(50), nullable=False)
    chargerType = db.Column(db.String(20), default='slow')
    status = db.Column(db.String(20), default='available')
    hourlyRate = db.Column(db.Float, default=2.50)
    lastUpdated = db.Column(db.DateTime, default=datetime.now)
    
    def json(self):
        return {
            "slotID": self.slotID,
            "stationID": self.stationID,
            "chargerType": self.chargerType,
            "status": self.status,
            "hourlyRate": self.hourlyRate,
            "lastUpdated": self.lastUpdated.strftime('%Y-%m-%d %H:%M:%S') if self.lastUpdated else None
        }


# ROUTES
# GET all slots
@app.route("/status/slots", methods=['GET'])
def get_all_slots():
    slots = ChargingSlot.query.all()
    
    if slots:
        return jsonify({
            "code": 200,
            "data": {
                "slots": [s.json() for s in slots]
            }
        })
    
    return jsonify({
        "code": 404,
        "message": "No slots found"
    }), 404


# GET slot by ID
@app.route("/status/<slotID>", methods=['GET'])
def get_slot(slotID):
    slot = db.session.get(ChargingSlot, slotID)
    
    if slot:
        return jsonify({
            "code": 200,
            "data": slot.json()
        })
    
    return jsonify({
        "code": 404,
        "message": f"Slot {slotID} not found"
    }), 404


# UPDATE slot status
@app.route("/status/<slotID>", methods=['PUT'])
def update_status(slotID):
    data = request.get_json()
    
    if not data or 'status' not in data:
        return jsonify({
            "code": 400,
            "message": "Missing required field: 'status'"
        }), 400
    
    new_status = data['status']
    valid_statuses = ['available', 'booked', 'occupied', 'faulty', 'maintenance']
    
    if new_status not in valid_statuses:
        return jsonify({
            "code": 400,
            "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        }), 400
    
    slot = db.session.get(ChargingSlot, slotID)
    
    if not slot:
        return jsonify({
            "code": 404,
            "message": f"Slot {slotID} not found"
        }), 404
    
    old_status = slot.status
    slot.status = new_status
    slot.lastUpdated = datetime.now()
    
    try:
        db.session.commit()
        
        return jsonify({
            "code": 200,
            "data": slot.json(),
            "message": f"Slot {slotID} status updated from {old_status} to {new_status}"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": str(e)
        }), 500


# GET slots by status (e.g., all faulty slots)
@app.route("/status/status/<status>", methods=['GET'])
def get_slots_by_status(status):
    valid_statuses = ['available', 'booked', 'occupied', 'faulty', 'maintenance']
    
    if status not in valid_statuses:
        return jsonify({
            "code": 400,
            "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        }), 400
    
    slots = ChargingSlot.query.filter_by(status=status).all()
    
    if slots:
        return jsonify({
            "code": 200,
            "data": {
                "slots": [s.json() for s in slots],
                "count": len(slots)
            }
        })
    
    return jsonify({
        "code": 404,
        "message": f"No slots found with status: {status}"
    }), 404


# GET available slots
@app.route("/status/available", methods=['GET'])
def get_available_slots():
    slots = ChargingSlot.query.filter_by(status='available').all()
    
    return jsonify({
        "code": 200,
        "data": {
            "slots": [s.json() for s in slots],
            "count": len(slots)
        }
    })


# GET faulty slots
@app.route("/status/faulty", methods=['GET'])
def get_faulty_slots():
    slots = ChargingSlot.query.filter_by(status='faulty').all()
    
    return jsonify({
        "code": 200,
        "data": {
            "slots": [s.json() for s in slots],
            "count": len(slots)
        }
    })


# DELETE slot
@app.route("/status/<slotID>", methods=['DELETE'])
def delete_slot(slotID):
    slot = db.session.get(ChargingSlot, slotID)
    
    if not slot:
        return jsonify({
            "code": 404,
            "message": f"Slot {slotID} not found"
        }), 404
    
    try:
        db.session.delete(slot)
        db.session.commit()
        return jsonify({
            "code": 200,
            "message": f"Slot {slotID} deleted successfully"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": str(e)
        }), 500


# RUN APP
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create sample data if table is empty
        if ChargingSlot.query.count() == 0:
            print("Creating sample slot data...")
            sample_slots = [
                ChargingSlot(slotID='SL001', stationID='ST001', chargerType='fast', status='available', hourlyRate=3.50),
                ChargingSlot(slotID='SL002', stationID='ST001', chargerType='slow', status='available', hourlyRate=2.00),
                ChargingSlot(slotID='SL003', stationID='ST001', chargerType='rapid', status='booked', hourlyRate=5.00),
                ChargingSlot(slotID='SL004', stationID='ST002', chargerType='fast', status='available', hourlyRate=3.50),
                ChargingSlot(slotID='SL005', stationID='ST002', chargerType='slow', status='faulty', hourlyRate=2.00),
                ChargingSlot(slotID='SL006', stationID='ST002', chargerType='fast', status='maintenance', hourlyRate=3.50),
            ]
            db.session.add_all(sample_slots)
            db.session.commit()
            print(f"Added {len(sample_slots)} sample slots")
    
    port = int(os.environ.get('PORT', 5004))
    print(f"Status Service running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)