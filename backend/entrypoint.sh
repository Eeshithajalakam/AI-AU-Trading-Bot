#!/bin/sh
set -e

# Optimized for free tier - reduced timeouts
RETRY_COUNT=20
RETRY_INTERVAL=2

echo "Waiting for database..."
python -c "
import asyncio
import sys
from sqlalchemy import text
from core.database import engine

async def wait():
    for i in range($RETRY_COUNT):
        try:
            async with engine.connect() as c:
                await c.execute(text('SELECT 1'))
            print('✓ Database ready')
            return
        except Exception as e:
            if i == $((RETRY_COUNT - 1)):
                print('✗ Database connection failed after retries')
                sys.exit(1)
            print(f'  Attempt {i+1}/$RETRY_COUNT: Waiting...')
            await asyncio.sleep($RETRY_INTERVAL)

asyncio.run(wait())
"

echo "Running migrations..."
alembic upgrade head

echo "Starting API (1 worker for free tier)..."
exec uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 1 \
  --loop uvloop \
  --interface asgi3
