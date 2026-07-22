FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r backend/requirements.txt \
    && playwright install --with-deps chromium

COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
