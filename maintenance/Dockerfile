
FROM python:3.10-slim

WORKDIR /app
# relative to docker build file
COPY maintenance/maintenance.py . 

COPY http.reqs.txt .

RUN pip install --no-cache-dir -r http.reqs.txt

CMD ["python", "maintenance.py"]
