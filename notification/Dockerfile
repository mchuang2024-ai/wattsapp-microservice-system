
FROM python:3.10-slim

WORKDIR /app
# relative to docker build file
COPY amqp.reqs.txt .
COPY http.reqs.txt .

RUN pip install --no-cache-dir -r http.reqs.txt -r amqp.reqs.txt
COPY notification/notification.py .
COPY notification/notification_amqp.py .
COPY notification/start.sh .
COPY rabbitmq/amqp_setup.py .
COPY amqp_lib.py invokes.py ./

RUN sed -i 's/\r$//' /app/start.sh \
    && chmod +x /app/start.sh

CMD ["sh", "/app/start.sh"]

