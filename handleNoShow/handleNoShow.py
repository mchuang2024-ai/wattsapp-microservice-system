from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import pika
import sys, os
from os import environ

import amqp_lib
from invokes import invoke_http

app = Flask(__name__)

CORS(app)

driverURL = environ.get("driverURL") 
bookingURL = environ.get("bookingURL")
paymentURL = environ.get("paymentURL")

# RabbitMQ
rabbit_host = environ.get("rabbit_host") 
rabbit_port = environ.get("rabbit_port") 
exchange_name = environ.get("exchange_name") 
exchange_type = environ.get("exchange_type") 

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
                exchange_name=exchange_name,
                exchange_type=exchange_type,
        )
    except Exception as exception:
        print(f"  Unable to connect to RabbitMQ.\n     {exception=}\n")
        exit(1) # terminate


@app.route("/handle-noshow", methods=["POST"])
def handleNoShow():
    #connect to AMQP if connection not established
    if connection is None or not amqp_lib.is_connection_open(connection):
        connectAMQP()
    #1 invoke the api
    if request.is_json:
        try:
            #get bookingID from request body
            bookingID = request.json.get("bookingID") 

            #2 calls booking service to retrieve the current booking status
            getBookingStatusURL = bookingURL + "/" + bookingID
            bookingStatus, bookingStatus_http_status = invoke_http(getBookingStatusURL, method='GET')

            if bookingStatus_http_status not in range(200, 300):
                    # Return error
                    return {
                        "code": 500,
                        "data": {"bookingStatus": bookingStatus },
                        "message": "Failure in retrieving booking status",
                    }, 500

            #if driver checks in late
            if driverchecksinlate:
                #3a Handle No-Show invokes Booking Service via HTTP PUT /booking/{bookingID}/checkin
                updateBookingStatusURL = bookingURL + "/" + bookingID + "/checkin"
                updateBookingStatusResult, updateBookingStatus_http_status = invoke_http(updateBookingStatusURL, method='PUT') 

                if updateBookingStatus_http_status not in range(200, 300):
                    # Return error
                    return {
                        "code": 500,
                        "data": {"updateBookingStatusResult": updateBookingStatusResult },
                        "message": "Failure in updating booking status to late check in",
                    }, 500

                # 4a. Handle No-Show invokes Payment Service via HTTP POST /payment/late-fee {bookingID, minsLate} to charge a proportional per-minute late fee against the driver's deposit.
                lateFeePaymentURL = paymentURL + "/late-fee"
                jsonData = jsonify({
                    "bookingID" : bookingID,
                    "minsLate" : 19
                })
                lateFeePaymentResult, lateFeePayment_http_status = invoke_http(lateFeePaymentURL, method="PUT", json=jsonData)

                if lateFeePayment_http_status not in range(200, 300):
                    # Return error
                    return {
                        "code": 500,
                        "data": {"lateFeePaymentResult": lateFeePaymentResult},
                        "message": "Failure to record late fee payment",
                    }, 500

                # 5a. Handle No-Show invokes Driver Service via HTTP PUT /driver/{driverID}/late-count to increment the driver's late arrival count.
                lateCountDriverURL = driverURL + "/" + driverID + "/late-count"
                lateCountDriverResult, lateCountDriver_http_status = invoke_http(lateCountDriverURL, method="PUT")

                if lateCountDriver_http_status not in range(200, 300):
                    # Return error
                    return {
                        "code": 500,
                        "data": {"lateCountDriverResult": lateCountDriverResult},
                        "message": "Failure to increment the driver's late arrival count",
                    }, 500

                # 6a. Handle No-Show publishes a late-charged event (bookingID, minsLate, feeAmount) to RabbitMQ Topic Exchange via AMQP.
                message = jsonify({
                    "bookingID": bookingID,
                    "minsLate" : 19,
                    "feeAmount": 20
                })
                channel.basic_publish(exchange=exchange_name, routing_key="late.charged", body=message)

            elif driverdoesnotshowup:
                # 3b. Handle No-Show invokes Booking Service via HTTP PUT /booking/{bookingID}/cancel. Booking Service updates the status to no_show.
                updateBookingStatusURL = bookingURL + "/" + bookingID + "/cancel"
                updateBookingStatusResult, updateBookingStatus_http_status = invoke_http(updateBookingStatusURL, method='PUT') 

                if updateBookingStatus_http_status not in range(200, 300):
                    # Return error
                    return {
                        "code": 500,
                        "data": {"updateBookingStatusResult": updateBookingStatusResult},
                        "message": "Failure to update the booking status to no_show",
                    }, 500

                # 4b. Handle No-Show invokes Driver Service to increase their late count (same as #5a)
                lateCountDriverURL = driverURL + "/" + driverID + "/late-count"
                lateCountDriverResult, lateCountDriver_http_status = invoke_http(lateCountDriverURL, method="PUT")

                if lateCountDriver_http_status not in range(200, 300):
                    # Return error
                    return {
                        "code": 500,
                        "data": {"lateCountDriverResult": lateCountDriverResult},
                        "message": "Failure to increment the driver's late arrival count",
                    }, 500

                # 5b. Handle No-Show invokes Payment Service to forfeit deposit
                forfeitDepositURL = paymentURL + "/forfeit-deposit"
                jsonData = jsonify({
                    "bookingID" : bookingID,
                })
                forfeitDepositResult, forfeitDeposit_http_status = invoke_http(forfeitDepositURL, method="POST", json=jsonData)

                if forfeitDeposit_http_status not in range(200, 300):
                    # Return error
                    return {
                        "code": 500,
                        "data": {"forfeitDepositResult": forfeitDepositResult},
                        "message": "Failure to forfeit deposit payment",
                    }, 500

                # 6b. Handle No-Show publishes a slot.released event (bookingID, slotID, stationID) to RabbitMQ Topic Exchange via AMQP.
                message = jsonify({
                    "bookingID": bookingID,
                    "slotID" : 19,
                    "stationID": 20
                })
                channel.basic_publish(exchange=exchange_name, routing_key="slot.released", body=message)


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

    else:
        return jsonify(
            {
                "code": 400,
                "message": "Invalid JSON input: " + str(request.get_data())
            }
        ), 400

# Execute this program if it is run as a main script (not by 'import')
if __name__ == "__main__":
    print("This is flask " + os.path.basename(__file__) + " for placing an order...")
    connectAMQP()
    app.run(host="0.0.0.0", port=5100, debug=True)