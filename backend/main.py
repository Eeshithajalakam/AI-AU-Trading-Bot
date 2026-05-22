import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.logging_config import setup_logging
from core.env_validation import log_environment_status
from core.middleware import RateLimitMiddleware
from core.startup import init_database
from core.deps import ai_service
from api.websockets import router as ws_router, market_data_broadcaster
from api.predictions import router as ai_router
from api.indicators import router as indicators_router
from api.signals import router as signals_router
from api.analytics import router as analytics_router
from api.mt5 import router as mt5_router
from api.settings import router as settings_router
from api.news import router as news_router
from api.backtest import router as backtest_router
from api.trades import router as trades_router
from api.training import router as training_router
from api.performance import router as performance_router
from services.market_engine import market_engine
from services.training_runner import run_training

logger = setup_logging()


async def _ensure_model_trained() -> None:
    model_path = Path(settings.resolved_model_path)
    if model_path.exists():
        ai_service.model_pipeline.load_model(settings.resolved_model_path, settings.scaler_path)
        logger.info("Loaded trained model from %s", model_path)
        return
    if not settings.AUTO_TRAIN_ON_STARTUP:
        logger.info("No model — set AUTO_TRAIN_ON_STARTUP=true or POST /api/training/train")
        return
    logger.info("Auto-training LSTM on startup...")
    try:
        await run_training(epochs=20, period="60d")
        logger.info("Startup training completed")
    except Exception as e:
        logger.warning("Startup training failed: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.MODEL_DIR).mkdir(parents=True, exist_ok=True)
    log_environment_status()

    try:
        await init_database()
        logger.info("Database initialized")
    except Exception as e:
        logger.error("Database init failed (continuing without DB): %s", e)

    await _ensure_model_trained()
    broadcaster = asyncio.create_task(market_data_broadcaster())
    logger.info("%s v%s ready", settings.PROJECT_NAME, settings.VERSION)

    yield

    broadcaster.cancel()
    try:
        await broadcaster
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-powered XAU/USD trading platform",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ws_router, tags=["websockets"])
app.include_router(ai_router)
app.include_router(indicators_router)
app.include_router(signals_router)
app.include_router(analytics_router)
app.include_router(mt5_router)
app.include_router(settings_router)
app.include_router(news_router)
app.include_router(backtest_router)
app.include_router(trades_router)
app.include_router(training_router)
app.include_router(performance_router)


@app.get("/")
async def root():
    return {
        "message": "AI AU Trading Backend API",
        "docs": "/docs",
        "websocket": "/ws/trading",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    from sqlalchemy import text
    from core.database import engine

    db_ok = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        pass

    return {
        "status": "healthy" if db_ok else "degraded",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_ok,
        "model_loaded": ai_service.model_pipeline.model_loaded,
        "model_exists": Path(settings.resolved_model_path).exists(),
        "market_symbol": settings.MARKET_SYMBOL,
        "current_price": market_engine.current_price,
        "market": market_engine.health_snapshot(),
        "auto_trade": settings.AUTO_TRADE_ENABLED,
        "paper_trading": settings.PAPER_TRADING_MODE,
        "signals_generated": ai_service.analytics["total_signals"],
    }
