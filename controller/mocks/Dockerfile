FROM python:3.14-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN pip install flask kubernetes

COPY controller/ controller/

ENV PYTHONPATH=/app

CMD ["python", "controller/mocks/mock_server.py"]