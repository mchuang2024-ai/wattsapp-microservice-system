from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import pika
import sys, os
from os import environ
import datetime

import amqp_lib
from invokes import invoke_http

app = Flask(__name__)

CORS(app)

driverURL = (environ.get("DRIVER_URL") or "http://localhost:5001")
bookingURL = (environ.get("BOOKING_URL") or "http://localhost:5002")
paymentURL = (environ.get("PAYMENT_URL") or "http://localhost:5003")

# RabbitMQ
rabbit_host = (environ.get("RABBIT_HOST") or "localhost")
rabbit_port = (environ.get("RABBIT_PORT") or 5672)
exchange_name = (environ.get("EXCHANGE_NAME") or "wattsapp_topic")
exchange_type = (environ.get("EXCHANGE_TYPE") or "topic")
username = (environ.get("RABBIT_USERNAME") or "admin")
password = (environ.get("RABBIT_PASSWORD") or "password123")

connection = None 
channel = None

def connectAMQP():
    # Use global variables to reduce number of reconnection to RabbitMQ
    # There are better ways but this suffices for our lab
    global connection
    global channel

    print("  Connecting to AMQP broker...")
    try:
        connection, channel = amqp_lib.connect(
            hostname=rabbit_host,
            port=rabbit_port,
            username=username,
            password=password,
            exchange_name=exchange_name,
            exchange_type=exchange_type,
        )
    except Exception as exception:
        print(f"  Unable to connect to RabbitMQ.\n     {exception=}\n")
        exit(1) # terminate

#handle no show (body:{bookingID, driverID, latecheckin(True or False)})
@app.route("/handle-noshow", methods=["POST"])
def handleNoShow():
    #connect to AMQP if connection not established
    if connection is None or not amqp_lib.is_connection_open(connection):
        connectAMQP()

    #1 
    if request.is_json:
        try:
            bookingID = request.json.get("bookingID") 
            driverID = request.json.get("driverID") 
            lateCheckIn = request.json.get("lateCheckIn")
            
            #2 
            booking, booking_http_status = invoke_http(f"{bookingURL}/booking/{bookingID}", method='GET')

            if booking_http_status not in range(200, 300):
                    # Return error
                    return jsonify({
                        "code": 500,
                        "data": {"booking": booking },
                        "message": "Failure in retrieving booking status",
                    }), 500


            if lateCheckIn == 'True':
                lateCheckIn = True
            else:
                lateCheckIn = False
            
            #3a
            if lateCheckIn:
                checkinTime = { "checkinTime" : str(datetime.datetime.now()) }
                updateBookingStatusResult, updateBookingStatus_http_status = invoke_http(f"{bookingURL}/booking/{bookingID}/checkin", method='PUT', json=checkinTime)
                    # Return error
                if updateBookingStatus_http_status not in range(200, 300):
                    return jsonify({
                        "code": 500,
                        "data": {"updateBookingStatusResult": updateBookingStatusResult },
                        "message": "Failure in updating booking status to late check in",
                    }), 500

                # 4a. 
                minsLate = booking["data"]["minsLate"]
                paymentData = {
                    "bookingID" : bookingID,
                    "driverID" : driverID,
                    "minsLate" : minsLate
                }
                lateFeePaymentResult, lateFeePayment_http_status = invoke_http(f"{paymentURL}/payment/late-fee", method="POST", json=paymentData)
                amount = lateFeePaymentResult["amount"]
                if lateFeePayment_http_status not in range(200, 300):
                    # Return error
                    return jsonify({
                        "code": 500,
                        "data": {"lateFeePaymentResult": lateFeePaymentResult},
                        "message": "Failure to record late fee payment",
                    }), 500

                # 5a. 
                lateCountDriverResult, lateCountDriver_http_status = invoke_http(f"{driverURL}/driver/{driverID}/late-count", method="PUT")

                if lateCountDriver_http_status not in range(200, 300):
                    # Return error
                    return jsonify({
                        "code": 500,
                        "data": {"lateCountDriverResult": lateCountDriverResult},
                        "message": "Failure to increment the driver's late arrival count",
                    }), 500

                # 6a. 
                message = json.dumps({
                    "bookingID": bookingID,
                    "minsLate" : minsLate,
                    "amount" : amount,
                    "message": "Your booking was checked in late. A late fee has been applied to your account."
                })
                channel.basic_publish(exchange=exchange_name, routing_key="late.charged", body=message)

            else:
                # 3b.
                updateBookingStatusResult, updateBookingStatus_http_status = invoke_http(f"{bookingURL}/booking/{bookingID}/cancel", method="PUT") 

                if updateBookingStatus_http_status not in range(200, 300):
                    # Return error
                    return jsonify({
                        "code": 500,
                        "data": {"updateBookingStatusResult": updateBookingStatusResult},
                        "message": "Failure to update the booking status to no_show",
                    }), 500

                # 4b. 
                lateCountDriverResult, lateCountDriver_http_status = invoke_http(f"{driverURL}/driver/{driverID}/late-count", method="PUT")

                if lateCountDriver_http_status not in range(200, 300):
                    # Return error
                    return jsonify({
                        "code": 500,
                        "data": {"lateCountDriverResult": lateCountDriverResult},
                        "message": "Failure to increment the driver's late arrival count",
                    }), 500

                # 5b. 
                paymentData = {
                    "bookingID" : bookingID,
                    "driverID" : driverID
                }
                forfeitDepositResult, forfeitDeposit_http_status = invoke_http(f"{paymentURL}/payment/forfeit-deposit", method="POST", json=paymentData)

                if forfeitDeposit_http_status not in range(200, 300):
                    # Return error
                    return jsonify({
                        "code": 500,
                        "data": {"forfeitDepositResult": forfeitDepositResult},
                        "message": "Failure to forfeit deposit payment",
                    }), 500

                # 6b. 
                message = json.dumps({
                    "bookingID": bookingID,
                    "message": "Your booking was marked as no-show. Your deposit has been forfeited."
                })
                channel.basic_publish(exchange=exchange_name, routing_key="slot.released", body=message)

            #final confirmation
            return jsonify(
                {
                    "code" : 201,
                    "message" : "successfully handled no-show."
                }
            ),201
            
        except Exception as e:
            # Unexpected error in code
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            ex_str = str(e) + " at " + str(exc_type) + ": " + fname + ": line " + str(exc_tb.tb_lineno)
            print("Error: {}".format(ex_str))

            return jsonify(
                    {
                        "code": 500,
                        "message": "handleNoShow.py internal error:",
                        "exception": ex_str,
                    }
            ), 500
        
    #invalid json exception
    else:
        return jsonify(
            {
                "code": 400,
                "message": "Invalid JSON input: " + str(request.get_data())
            }
        ), 400

# Execute this program if it is run as a main script (not by 'import')
if __name__ == "__main__":
    print("This is flask " + os.path.basename(__file__) + " handling no show..")
    connectAMQP()
    app.run(host="0.0.0.0", port=5100, debug=True)
