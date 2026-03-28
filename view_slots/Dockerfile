FROM python:3.10-slim

WORKDIR /app

COPY view_slots/view_slots.py .
COPY view_slots/config.py .
COPY http.reqs.txt .

RUN pip install --no-cache-dir -r http.reqs.txt

CMD ["python", "view_slots.py"]