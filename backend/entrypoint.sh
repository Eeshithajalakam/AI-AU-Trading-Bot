#!/bin/sh
set -e
echo "Waiting for database..."
python -c "
import asyncio, time, sys
from sqlalchemy import text
from core.database import engine

async def wait():
    for i in range(30):
        try:
            async with engine.connect() as c:
                await c.execute(text('SELECT 1'))
            print('DB ready')
            return
        except Exception as e:
            print(f'Attempt {i+1}: {e}')
            await asyncio.sleep(2)
    sys.exit(1)

asyncio.run(wait())
"

echo "Running migrations..."
alembic upgrade head

echo "Starting API..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
