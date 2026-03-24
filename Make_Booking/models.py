from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Optional DB persistence
# app imports db from this module

db = SQLAlchemy()


class BookingLog(db.Model):
    __tablename__ = 'booking_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    driverID = db.Column(db.Integer, nullable=False)
    chargerID = db.Column(db.Integer, nullable=False)
    starttime = db.Column(db.DateTime, nullable=False)
    endtime = db.Column(db.DateTime, nullable=False)
    deposit = db.Column(db.Float, nullable=False)
    bookingID = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'driverID': self.driverID,
            'chargerID': self.chargerID,
            'starttime': self.starttime.isoformat() if self.starttime else None,
            'endtime': self.endtime.isoformat() if self.endtime else None,
            'deposit': self.deposit,
            'bookingID': self.bookingID,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }