from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ
import os
app = Flask(__name__)
CORS(app)  # Allow frontend access


# Railway MySQL connection (replace with your vars)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or \
    "mysql+mysqlconnector://root:jpPOaVCbCXnTWjDOBzPtDoRKYwqqiClR@caboose.proxy.rlwy.net:45033/driver"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)

class Driver(db.Model):
    __tablename__ = 'Drivers'
    driverID = db.Column(db.Integer, primary_key=True)
    late_count = db.Column(db.Integer, default=0)
    telegram_chat_id = db.Column(db.Integer, default= None)
    
    def json(self):
        return {'driverID': self.driverID, 'late_count': self.late_count, 'telegram_chat_id': self.telegram_chat_id}

@app.route("/drivers", methods=['GET'])
def get_all():
    drivers = db.session.scalars(db.select(Driver)).all()
    return jsonify({"code": 200, "data": {"drivers": [d.json() for d in drivers]}})

@app.route("/drivers", methods=['POST'])
def create_driver():
    try:
        data = request.get_json()
        driver = Driver(
            driverID=data.get('driverID'),
            late_count=data.get('late_count', 0)
        )
        
        db.session.add(driver)
        db.session.commit()
        
        return jsonify({
            "code": 201,
            "data": driver.json(),
            "message": "Driver created successfully"
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "error": str(e)}), 500
    
@app.route("/drivers/<int:driver_id>", methods=['GET'])
def get_driver(driver_id):
    try:
        driver = db.session.scalar(db.select(Driver).where(Driver.driverID == driver_id))
        
        if not driver:
            return jsonify({"code": 404, "error": "Driver not found"}), 404
        
        return jsonify({
            "code": 200,
            "data": driver.json()
        }), 200
    
    except Exception as e:
        return jsonify({"code": 500, "error": str(e)}), 500

@app.route("/drivers/<int:driver_id>/telegram", methods=['POST'])
def update_telegram_chat(driver_id):
    try:
        data = request.get_json()
        chat_id = data.get('telegram_chat_id')
        
        driver = db.session.scalar(db.select(Driver).where(Driver.driverID == driver_id))
        if not driver:
            return jsonify({"code": 404, "error": "Driver not found"}), 404
        
        driver.telegram_chat_id = chat_id
        db.session.commit()
        
        return jsonify({
            "code": 200,
            "data": driver.json(),
            "message": "Telegram chat ID updated"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "error": str(e)}), 500

@app.route("/driver/<int:driver_id>/late-count", methods=['PUT'])
def add_late_count(driver_id):
    try:
        driver = db.session .scalar(db.select(Driver).where(Driver.driverID == driver_id))
        if not driver:
            return jsonify({
                "code" : 404,
                "message" : f"No driver with driverID = {driver_id} found"
             })
        late_count = driver.late_count + 1
        driver.late_count = late_count
        db.session.commit()
        return jsonify({
            "code" : 200,
            "message" : f"Driver late-count added by 1, currently {late_count}"
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"unexpected error: {e}"
        })
        

if __name__ == '__main__':
    print("Driver Service: Port 5001")
    app.run(host='0.0.0.0', port=5001, debug=True)