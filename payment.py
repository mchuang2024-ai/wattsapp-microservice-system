from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ
from datetime import datetime
import os

app = Flask(__name__)

CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    environ.get('dbURL')
)

db = SQLAlchemy(app)

class Payment(db.Model):
    __tablename__ = 'payment'
    
    paymentID = db.Column(db.integer, primary_key = True, nullable = False)
    driverID = db.Column(db.integer, nullable = False) #foreign key
    bookingID = db.Column(db.integer, nullable = False) #foreign key
    amount = db.Column(db.float, nullable = False) 
    type = db.Column(db.string(10), nullable = False, default = 'hold') 
    status = db.Column(db.string(10), nullable = False, default = 'pending')
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
    
# Make Payment
@app.route("/payment/hold", methods=['POST'])
def makePayment():
    pass

#Extra Payment if Late
@app.route("/payment/late-fee", methods=['POST'])
def extraPayment():
    pass

#Penalty (Deposit Paid)
@app.route("/payment/forfeit-deposit", methods=['POST'])
def penalty():
    pass
    
    
if __name__ == '__main__':
    print("This is flask for " + os.path.basename(__file__) + ": manage payments ...")
    app.run()

# @app.route("/order", methods=['POST'])
# def create_order():
#     customer_id = request.json.get('customer_id', None)
#     order = Order(customer_id=customer_id, status='NEW')

#     cart_item = request.json.get('cart_item')
#     for item in cart_item:
#         order.order_item.append(Order_Item(
#             book_id=item['book_id'], quantity=item['quantity']))

#     try:
#         db.session.add(order)
#         db.session.commit()
#     except Exception as e:
#         print("Error: {}".format(str(e)))
#         return jsonify(
#             {
#                 "code": 500,
#                 "message": "An error occurred while creating the order. " + str(e)
#             }
#         ), 500

#     return jsonify(
#         {
#             "code": 201,
#             "data": order.json()
#         }
#     ), 201





