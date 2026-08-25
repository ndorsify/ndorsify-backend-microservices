# messaging-service — FastAPI (uvicorn) on port 3000
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=3000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

EXPOSE 3000
# Apply migrations (Postgres schema is Alembic-owned), then start the server.
CMD ["sh", "-c", "alembic upgrade head && python -m app.server"]
