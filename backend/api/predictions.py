from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import pandas as pd

from ai.service import AIService

router = APIRouter(prefix="/ai", tags=["AI Predictions"])

# Initialize the AI Service
# Note: In a production app, you might use FastAPI dependencies for this.
ai_service = AIService()

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
    data: List[OHLCVData]

class SignalResponse(BaseModel):
    timestamp: str
    asset: str
    current_price: float
    predicted_price: float
    action: str
    trend: str
    confidence_score: float
    timeframes_analyzed: List[str]
    metrics: Dict[str, Any]

@router.post("/predict", response_model=SignalResponse)
async def generate_prediction(request: PredictionRequest):
    """
    Endpoint to generate an AI trading prediction based on OHLCV history.
    Requires at least 50 historical data points to compute valid indicators.
    """
    if request.symbol != "XAU/USD":
        raise HTTPException(status_code=400, detail="Only XAU/USD is supported currently.")
        
    if len(request.data) < 50:
        raise HTTPException(status_code=400, detail="Minimum 50 data points required for analysis.")

    # Convert request data to a Pandas DataFrame
    records = [
        {
            "timestamp": pd.to_datetime(d.timestamp),
            "open": d.open,
            "high": d.high,
            "low": d.low,
            "close": d.close,
            "volume": d.volume
        }
        for d in request.data
    ]
    df = pd.DataFrame(records).set_index("timestamp")

    try:
        signal = await ai_service.analyze_market_data(df)
        return signal
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Analysis failed: {str(e)}")

@router.get("/status")
async def get_ai_status():
    """
    Endpoint to check the status of the AI model pipeline.
    """
    return {
        "status": "online",
        "model": "LSTM-XAUUSD-v1.0",
        "device": str(ai_service.model_pipeline.device)
    }
