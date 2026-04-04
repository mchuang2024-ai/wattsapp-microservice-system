import os

# Database logging (optional)
SQLALCHEMY_DATABASE_URI = os.environ.get(
    'SQLALCHEMY_DATABASE_URI',
    'mysql+mysqlconnector://root:rootpass@localhost:3306/pulsepark'
)

# RabbitMQ
type = 'amqp'
RABBITMQ_URL = os.environ.get('RABBITMQ_URL', 'amqp://admin:password123@localhost:5672/%2F')

# Downstream service URLs
PAYMENT_URL = os.environ.get('PAYMENT_URL', 'http://localhost:5003/payment/hold')
BOOKING_URL = os.environ.get('BOOKING_URL', 'http://localhost:5002/booking')
DRIVER_URL = os.environ.get('DRIVER_URL', 'http://localhost:5001')
