FROM python:3.12-slim AS base
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg curl postgresql-client \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
ENV PYTHONPATH=/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS runtime
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./alembic.ini
COPY scripts ./scripts
RUN test -f /app/alembic.ini \
    && test -f /app/migrations/env.py \
    && test -f /app/migrations/versions/0008_rate_limit_buckets.py
RUN useradd --system --uid 10001 --create-home appuser && chown -R appuser:appuser /app
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]

FROM base AS test
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini .
COPY scripts ./scripts
COPY tests ./tests
COPY Dockerfile docker-compose.dev.yml docker-compose.test.yml docker-compose.e1.test.yml docker-compose.g5.yml .env.dev.example .gitignore ./
RUN useradd --system --uid 10001 --create-home appuser && chown -R appuser:appuser /app
USER appuser
CMD ["pytest", "-q"]
