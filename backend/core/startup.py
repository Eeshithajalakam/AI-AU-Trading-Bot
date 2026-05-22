"""Application startup: DB migrations and connectivity checks."""

import asyncio
import logging
from pathlib import Path

import subprocess
import sys
from sqlalchemy import text

from core.config import settings
from core.database import engine

logger = logging.getLogger(__name__)


async def wait_for_database(max_retries: int = 30, delay: float = 2.0) -> bool:
    for attempt in range(1, max_retries + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database connection established")
            return True
        except Exception as e:
            logger.warning("DB not ready (attempt %d/%d): %s", attempt, max_retries, e)
            await asyncio.sleep(delay)
    return False


def run_migrations() -> None:
    backend_dir = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(backend_dir),
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "DATABASE_URL": settings.DATABASE_URL},
    )
    if result.returncode != 0:
        logger.error("Alembic failed: %s", result.stderr)
        raise RuntimeError(result.stderr or "Migration failed")
    logger.info("Alembic migrations applied")


async def init_database() -> None:
    if not await wait_for_database():
        raise RuntimeError("Could not connect to PostgreSQL")
    await asyncio.to_thread(run_migrations)
