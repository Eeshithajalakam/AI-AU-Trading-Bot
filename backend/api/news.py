from fastapi import APIRouter
from ai.news_intelligence import news_engine

router = APIRouter(prefix="/api/news", tags=["Macro Intelligence"])

@router.get("/macro")
async def get_macro_environment():
    """Retrieve live AI sentiment analysis and macroeconomic event risks."""
    return news_engine.analyze_current_environment()
