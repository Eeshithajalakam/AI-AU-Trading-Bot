import logging
import sys
from core.config import settings


def setup_logging() -> logging.Logger:
    level = logging.DEBUG if settings.DEBUG else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    return logging.getLogger(settings.PROJECT_NAME)
