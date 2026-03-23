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
    result = 1 + 1
    return result
    
if __name__ == '__main__':
    print("This is flask for " + os.path.basename(__file__) + ": manage payments ...")
    app.run(host='0.0.0.0', port=5001, debug=True)

# @app.route("/order/<string:order_id>")
# def find_by_order_id(order_id):
#     order = db.session.scalar(db.select(Order).filter_by(order_id=order_id))
#     if order:
#         return jsonify(
#             {
#                 "code": 200,
#                 "data": order.json()
#             }
#         )
#     return jsonify(
#         {
#             "code": 404,
#             "data": {
#                 "order_id": order_id
#             },
#             "message": "Order not found."
#         }
#     ), 404


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


# @app.route("/order/<string:order_id>", methods=['PUT'])
# def update_order(order_id):
#     try:
#         order = db.session.scalar(db.select(Order).filter_by(order_id=order_id))
#         if not order:
#             return jsonify(
#                 {
#                     "code": 404,
#                     "data": {
#                         "order_id": order_id
#                     },
#                     "message": "Order not found."
#                 }
#             ), 404

#         # update status
#         data = request.get_json()
#         if data['status']:
#             order.status = data['status']
#             db.session.commit()
#             return jsonify(
#                 {
#                     "code": 200,
#                     "data": order.json()
#                 }
#             ), 200
#     except Exception as e:
#         print("Error: {}".format(str(e)))
#         return jsonify(
#             {
#                 "code": 500,
#                 "data": {
#                     "order_id": order_id
#                 },
#                 "message": "An error occurred while updating the order. " + str(e)
#             }
#         ), 500


