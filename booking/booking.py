from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ
from datetime import datetime
from sqlalchemy import func


app = Flask(__name__)

CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('DATABASE_URL') or \
    "mysql+mysqlconnector://root:jpPOaVCbCXnTWjDOBzPtDoRKYwqqiClR@caboose.proxy.rlwy.net:45033/booking"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}
db = SQLAlchemy(app)


class Bookings(db.Model):
    __tablename__ = "Bookings"

    bookingID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    driverID = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    startTime = db.Column(db.DateTime, nullable=False)
    endTime = db.Column(db.DateTime, nullable=False)
    minsLate = db.Column(db.Integer, default=0)
    slotID = db.Column(db.Integer, nullable=False)
    depositAmount = db.Column(db.Float(precision=2), nullable=False)

    def __init__(self, driverID, status, startTime, endTime, slotID, depositAmount, minsLate=0):
        self.driverID = driverID
        self.status = status
        self.startTime = startTime
        self.endTime = endTime
        self.minsLate = minsLate
        self.slotID = slotID
        self.depositAmount = depositAmount

    def json(self):
        return {
            "bookingID": self.bookingID,
            "driverID": self.driverID,
            "status": self.status,
            "startTime": str(self.startTime),
            "endTime": str(self.endTime),
            "minsLate": self.minsLate,
            "slotID": self.slotID,
            "depositAmount": self.depositAmount,
        }

with app.app_context():
    db.create_all()
    print("Booking database tables created successfully.")

# get all bookings
@app.route("/booking")
def get_all_bookings():
    bookings = db.session.scalars(db.select(Bookings)).all()

    if len(bookings):
        return jsonify(
            {
                "code": 200,
                "data": {"bookings": [booking.json() for booking in bookings]},
            }
        )
    return jsonify({"code": 404, "message": "There are no bookings."}), 404

# get a particular booking
@app.route("/booking/<int:bookingID>")
def get_booking(bookingID):
    booking = db.session.scalar(db.select(Bookings).filter_by(bookingID=bookingID))

    if booking:
        return jsonify({"code": 200, "data": booking.json()})
    return jsonify({"code": 404, "message": "Booking not found."}), 404

# get all bookings for a specific slot
@app.route("/booking/slot/<int:slotID>")
def get_bookings_by_slot(slotID):
    bookings = db.session.scalars(db.select(Bookings).filter_by(slotID=slotID)).all()
    return jsonify({"code": 200, "data": {"bookings": [b.json() for b in bookings]}})

# get only uncancelled bookings for a date
@app.route("/booking/date/<date_str>")
def get_bookings_by_date(date_str):
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Extract only the date from startTime and compare
        bookings = db.session.scalars(
            db.select(Bookings).where(
                (func.date(Bookings.startTime) == target_date) &
                (Bookings.status != "cancelled")
            )
        ).all()
        
        if len(bookings):
            return jsonify({
                "code": 200,
                "data": {"bookings": [booking.json() for booking in bookings]},
                "date": date_str,
                "count": len(bookings)
            }), 200
        return jsonify({"code": 404, "message": f"No bookings found for {date_str}"}), 404
    except ValueError:
        return jsonify({"code": 400, "message": "Invalid date format. Use YYYY-MM-DD"}), 400
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500
    
# make a booking
@app.route("/booking", methods=["POST"])
def create_booking():
    data = request.get_json()
    required = ["driverID", "startTime", "endTime", "slotID"]
    if not all(field in data for field in required):
        return jsonify({"code": 400, "message": "Missing required fields."}), 400

    booking = Bookings(
        driverID=data["driverID"],
        status="upcoming",  
        startTime=data["startTime"],
        endTime=data["endTime"],
        slotID=data["slotID"],
        depositAmount=5.0,  
        minsLate=0
    )

    try:
        db.session.add(booking)
        db.session.commit()
    except Exception as e:
        print("Exception:{}".format(str(e)))
        return (
            jsonify(
                {
                    "code": 500,
                    "message": "An error occurred creating the booking.",
                }
            ),
            500,
        )

    return jsonify({"code": 201, "data": booking.json()}), 201


# Update status to checkin. if earlier than starttime, reject. 
# if exactly on time or later, will calculate how many min late. floor div
# Needs checkintime in request body
# {
#   "checkinTime": "2026-03-20 08:05:00"
# }
@app.route("/booking/<int:bookingID>/checkin", methods=["PUT"])
def update_checkin(bookingID):
    booking = db.session.scalar(db.select(Bookings).filter_by(bookingID=bookingID))
    if not booking:
        return jsonify({"code": 404, "message": "Booking not found."}), 404
    
    data = request.get_json()
    if not data or "checkinTime" not in data:
        return jsonify({"code": 400, "message": "Missing checkinTime in request."}), 400

    try:
        checkin_time = datetime.strptime(data["checkinTime"], '%Y-%m-%d %H:%M:%S')
    except Exception:
        return jsonify({"code": 400, "message": "Invalid checkinTime format. Use: YYYY-MM-DD HH:MM:SS"}), 400

    if checkin_time < booking.startTime:
        return jsonify({"code": 400, "message": "Too early to check in."}), 400

    mins_late = int((checkin_time - booking.startTime).total_seconds() // 60)
    booking.status = "checked-in"
    booking.minsLate = mins_late 
    db.session.commit()
    return jsonify({"code": 200, "data": booking.json()})


# Update status to no_show
@app.route("/booking/<int:bookingID>/noshow", methods=["PUT"])
def noshow_booking(bookingID):
    booking = db.session.scalar(db.select(Bookings).filter_by(bookingID=bookingID))
    if not booking:
        return jsonify({"code": 404, "message": "Booking not found."}), 404
    booking.status = "no_show"
    db.session.commit()
    return jsonify({"code": 200, "data": booking.json()})

# Update status to cancelled
@app.route("/booking/<int:bookingID>/cancel", methods=["PUT"])
def cancel_booking(bookingID):
    booking = db.session.scalar(db.select(Bookings).filter_by(bookingID=bookingID))
    if not booking:
        return jsonify({"code": 404, "message": "Booking not found."}), 404
    
    booking.status = "cancelled"
    db.session.commit()
    return jsonify({"code": 200, "data": booking.json()})


# Delete a booking
@app.route("/booking/<int:bookingID>", methods=["DELETE"])
def delete_booking(bookingID):
    booking = db.session.scalar(db.select(Bookings).filter_by(bookingID=bookingID))
    if not booking:
        return jsonify({"code": 404, "message": "Booking not found."}), 404
    
    db.session.delete(booking)
    db.session.commit()
    return jsonify({"code": 200, "message": "Booking deleted."}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
