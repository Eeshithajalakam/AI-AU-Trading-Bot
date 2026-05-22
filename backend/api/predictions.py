from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any

import pandas as pd

from core.deps import ai_service

router = APIRouter(prefix="/ai", tags=["AI Predictions"])


class OHLCVData(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class PredictionRequest(BaseModel):
    symbol: str
    timeframe: str
    data: list[OHLCVData]


@router.post("/predict")
async def generate_prediction(request: PredictionRequest):
    if request.symbol != "XAU/USD":
        raise HTTPException(status_code=400, detail="Only XAU/USD is supported currently.")
    if len(request.data) < 50:
        raise HTTPException(status_code=400, detail="Minimum 50 data points required for analysis.")

    records = [
        {
            "timestamp": pd.to_datetime(d.timestamp),
            "open": d.open,
            "high": d.high,
            "low": d.low,
            "close": d.close,
            "volume": d.volume,
        }
        for d in request.data
    ]
    df = pd.DataFrame(records).set_index("timestamp")

    try:
        return await ai_service.analyze_market_data(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Analysis failed: {str(e)}")


@router.get("/status")
async def get_ai_status():
    return {
        "status": "online",
        "model": "LSTM-XAUUSD",
        "model_loaded": ai_service.model_pipeline.model_loaded,
        "device": str(ai_service.model_pipeline.device),
        "analytics": ai_service.analytics,
    }
