from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from api.websockets import router as ws_router, market_data_broadcaster
from api.predictions import router as ai_router
from api.indicators import router as indicators_router
from api.signals import router as signals_router
from api.analytics import router as analytics_router
from api.mt5 import router as mt5_router
from api.settings import router as settings_router
from api.news import router as news_router
from api.backtest import router as backtest_router
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create background tasks
    task = asyncio.create_task(market_data_broadcaster())
    yield
    # Shutdown: Clean up background tasks
    task.cancel()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(ws_router, tags=["websockets"])
app.include_router(ai_router)
app.include_router(indicators_router)
app.include_router(signals_router)
app.include_router(analytics_router)
app.include_router(mt5_router)
app.include_router(settings_router)
app.include_router(news_router)
app.include_router(backtest_router)

@app.get("/")
async def root():
    return {"message": "AI Trading Backend API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}
