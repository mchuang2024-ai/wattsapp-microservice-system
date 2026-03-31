
FROM python:3.10-slim

WORKDIR /app
# relative to docker build file
COPY notification/notification.py .
COPY notification/notification_amqp.py .
COPY notification/start.sh .
# COPY rabbitmq/amqp_setup.py .
COPY amqp.reqs.txt .
COPY http.reqs.txt .

RUN pip install --no-cache-dir -r http.reqs.txt -r amqp.reqs.txt
COPY amqp_lib.py invokes.py ./

RUN chmod +x start.sh

CMD ["sh", "start.sh"]


