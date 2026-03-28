FROM python:3.10-slim
WORKDIR /app
COPY Make_Booking/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY amqp_lib.py invokes.py ./
COPY Make_Booking/app.py .
CMD ["python", "app.py"]