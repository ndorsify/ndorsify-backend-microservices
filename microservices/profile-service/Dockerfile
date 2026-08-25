# profile-service — FastAPI (uvicorn) on port 6000
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=6000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

EXPOSE 6000
# Apply migrations (Postgres schema is Alembic-owned), then start the server.
CMD ["sh", "-c", "alembic upgrade head && python -m app.server"]
