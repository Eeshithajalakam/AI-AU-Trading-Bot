"""Validate critical environment settings at startup."""

import logging
import sys

from core.config import settings

logger = logging.getLogger(__name__)


def validate_environment() -> list[str]:
    warnings: list[str] = []

    if settings.SECRET_KEY == "super-secret-jwt-key-replace-in-production":
        if settings.ENVIRONMENT == "production":
            warnings.append("SECRET_KEY must be changed in production")

    if settings.AUTO_TRADE_ENABLED and not settings.PAPER_TRADING_MODE:
        if not settings.mt5_login:
            warnings.append("AUTO_TRADE_ENABLED but MT5_LOGIN is not set")

    if "localhost" in settings.DATABASE_URL and settings.ENVIRONMENT == "production":
        warnings.append("DATABASE_URL points to localhost in production")

    return warnings


def log_environment_status() -> None:
    issues = validate_environment()
    for msg in issues:
        logger.warning("ENV: %s", msg)
    if issues and settings.ENVIRONMENT == "production":
        logger.error("Critical environment issues detected")
    logger.info(
        "Config: env=%s auto_trade=%s paper=%s auto_train=%s",
        settings.ENVIRONMENT,
        settings.AUTO_TRADE_ENABLED,
        settings.PAPER_TRADING_MODE,
        settings.AUTO_TRAIN_ON_STARTUP,
    )
