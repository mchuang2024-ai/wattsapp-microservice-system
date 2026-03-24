from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ
from datetime import datetime
import os

app = Flask(__name__)

CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = (environ.get('dbURL'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)

class Payment(db.Model):
    __tablename__ = 'Payment'
    
    paymentID = db.Column(db.Integer, primary_key = True, nullable = False)
    driverID = db.Column(db.Integer, nullable = False)
    bookingID = db.Column(db.Integer, nullable = False) 
    amount = db.Column(db.Float, nullable = False, default = 0.0) 
    type = db.Column(db.String(10), nullable = False) 
    status = db.Column(db.String(10), nullable = False, default = 'pending')
    createdAt = db.Column(db.DateTime, nullable = False, default = datetime.now)
    
    def json(self):
        dto = {
            'paymentID': self.paymentID,
            'driverID': self.driverID,
            'bookingID': self.bookingID,
            'amount': self.amount,
            'type': self.type,
            'status': self.status,
            'createdAt': self.createdAt.isoformat(),
        }
        return dto
    
# Make Payment (Create a new payment record)
@app.route("/payment/hold", methods=['POST'])
def makePayment():
    driverID = request.json.get('driverID', None)
    bookingID = request.json.get('bookingID', None)
    amount = request.json.get('amount', None)

    payment = Payment(driverID=driverID, bookingID=bookingID, amount=amount, type='hold')

    try:
        db.session.add(payment)
        db.session.commit()

    except Exception as e:
        print("Error: {}".format(str(e)))
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred while recording the payment. " + str(e)
            }
        ), 500

    return jsonify(
        {
            "code": 201,
            "data": payment.json()
        }
    ), 201

#Extra Payment if Late (Create a new payment record)
@app.route("/payment/late-fee", methods=['POST'])
def extraPayment():
    bookingID = request.json.get('bookingID', None)
    driverID = request.json.get('driverID', None)
    minsLate = request.json.get('minsLate', None)

    # Calculate the late fee based on the number of minutes late
    late_fee = minsLate * 0.1  # Example calculation, adjust as needed

    payment = Payment(bookingID=bookingID, driverID=driverID, amount=late_fee, type='late-fee')

    try:
        db.session.add(payment)
        db.session.commit()
        
    except Exception as e:
        print("Error: {}".format(str(e)))
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred while recording the late fee payment. " + str(e)
            }
        ), 500

    return jsonify(
        {
            "code": 201,
            "data": payment.json()
        }
    ), 201

#Penalty (Deposit Paid)
@app.route("/payment/forfeit-deposit", methods=['POST'])
def penaltyPayment():
    bookingID = request.json.get('bookingID', None)
    driverID = request.json.get('driverID', None)
    
    payment = Payment(bookingID=bookingID, driverID=driverID, type='forfeit', status='pending')

    try:
        db.session.add(payment)
        db.session.commit()
        
    except Exception as e:
        print("Error: {}".format(str(e)))
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred while recording the forfeit deposit payment. " + str(e)
            }
        ), 500

    return jsonify(
        {
            "code": 201,
            "data": payment.json()
        }
    ), 201
    
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)






