FROM python:3.9-slim

WORKDIR /app

COPY controller/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY controller/ controller/

ENV PYTHONPATH=/app

CMD ["python", "controller/epigenetic_controller.py"]
