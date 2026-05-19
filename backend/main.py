from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from api.websockets import router as ws_router, market_data_broadcaster
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

@app.get("/")
async def root():
    return {"message": "AI Trading Backend API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}
