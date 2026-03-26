FROM python:3.10

WORKDIR /app
COPY http.reqs.txt .
RUN pip install -r http.reqs.txt

COPY report_fault/report_fault.py .

CMD ["python", "report_fault.py"]