FROM python:3.12-slim AS base
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS runtime
COPY app ./app
RUN useradd --system --uid 10001 --create-home appuser && chown -R appuser:appuser /app
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]

FROM base AS test
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini .
COPY scripts ./scripts
COPY tests ./tests
RUN useradd --system --uid 10001 --create-home appuser && chown -R appuser:appuser /app
USER appuser
CMD ["pytest", "-q"]
