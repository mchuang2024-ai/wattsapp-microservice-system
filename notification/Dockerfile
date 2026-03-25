
FROM python:3.10-slim

WORKDIR /app
# relative to docker build file
COPY notification/notification.py .
COPY rabbitmq/amqp_setup.py .
COPY amqp.reqs.txt .
COPY http.reqs.txt .

RUN pip install --no-cache-dir -r http.reqs.txt -r amqp.reqs.txt

CMD ["python", "notification.py"]


