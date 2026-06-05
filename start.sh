#!/bin/sh

echo "Ejecutando migraciones..."

alembic upgrade head

echo "Iniciando FastAPI..."

gunicorn app.main:app \
-k uvicorn.workers.UvicornWorker \
-w 4 \
-b 0.0.0.0:8000