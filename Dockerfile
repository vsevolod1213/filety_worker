FROM python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir fastapi uvicorn

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY handler.py .

CMD ["python", "-u", "handler.py"]

