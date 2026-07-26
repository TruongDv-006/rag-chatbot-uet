#!/bin/sh

echo "[Worker Startup] Running automatic ingestion for web json and parsed docs..."
python3 -m worker.ingestion.ingester || echo "[Worker Startup] Ingestion notice: continued to worker."

echo "[Worker Startup] Starting Celery worker..."
exec celery -A task worker --loglevel=info
