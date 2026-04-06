from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

app = Flask(__name__)

# DATABASE CONFIG (Railway)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('dbURL',
    'mysql+mysqlconnector://root:jpPOaVCbCXnTWjDOBzPtDoRKYwqqiClR@caboose.proxy.rlwy.net:45033/maintenance')
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)
CORS(app)

# MODEL
class MaintenanceTicket(db.Model):
    __tablename__ = 'MaintenanceTicket'

    ticketID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    slotID = db.Column(db.String(50), nullable=False)
    reportedBy = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255))
    chargerType = db.Column(db.String(50))
    status = db.Column(db.String(20), default='OPEN')

    def json(self):
        return {
            "ticketID": self.ticketID,
            "slotID": self.slotID,
            "reportedBy": self.reportedBy,
            "description": self.description,
            "chargerType": self.chargerType,
            "status": self.status
        }

with app.app_context():
    db.create_all()
    print("Maintenance database tables created successfully.")

# ROUTES
# CREATE TICKET
@app.route("/maintenance/ticket", methods=['POST'])
def create_ticket():
    data = request.get_json()

    if not data or 'slotID' not in data or 'reportedBy' not in data:
        return jsonify({
            "code": 400,
            "message": "Missing required fields"
        }), 400

    ticket = MaintenanceTicket(
        slotID=data['slotID'],
        reportedBy=data['reportedBy'],
        description=data.get('description'),
        chargerType=data.get('chargerType')
    )

    try:
        db.session.add(ticket)
        db.session.commit()
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": str(e)
        }), 500

    return jsonify({
        "code": 201,
        "data": ticket.json()
    }), 201

# GET ALL TICKETS
@app.route("/maintenance/tickets", methods=['GET'])
def get_all_tickets():
    tickets = MaintenanceTicket.query.all()
    
    if tickets:
        return jsonify({
            "code": 200,
            "data": {
                "tickets": [t.json() for t in tickets]
            }
        })
    
    return jsonify({
        "code": 404,
        "message": "No tickets found"
    }), 404


# GET TICKET BY ID
@app.route("/maintenance/ticket/<int:id>", methods=['GET'])
def get_ticket(id):
    ticket = db.session.get(MaintenanceTicket, id)

    if ticket:
        return jsonify({
            "code": 200,
            "data": ticket.json()
        })

    return jsonify({
        "code": 404,
        "message": "Ticket not found"
    }), 404


# UPDATE STATUS
@app.route("/maintenance/ticket/<int:id>/status", methods=['PUT'])
def update_status(id):
    data = request.get_json()

    ticket = db.session.get(MaintenanceTicket, id)

    if not ticket:
        return jsonify({
            "code": 404,
            "message": "Ticket not found"
        }), 404

    ticket.status = data.get('status', ticket.status)
    db.session.commit()

    return jsonify({
        "code": 200,
        "data": ticket.json()
    })




# RUN APP
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables created/verified")
    app.run(host='0.0.0.0', port=5005, debug=True)