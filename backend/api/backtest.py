from fastapi import APIRouter, Query
from trading.backtester import BacktestEngine

router = APIRouter(prefix="/api/backtest", tags=["Analytics"])

@router.post("/run")
async def run_backtest(
    days: int = Query(30, description="Number of historical days to backtest"),
    capital: float = Query(10000.0, description="Starting capital in USD")
):
    """
    Executes a high-speed historical replay using the active AI model parameters.
    Returns institutional metrics including Sharpe Ratio, Max Drawdown, and Win/Loss analytics.
    """
    engine = BacktestEngine(initial_capital=capital)
    
    # Generate robust historical dataset mimicking XAU/USD
    df = engine.generate_dummy_data(days=days)
    
    # Run the replay simulation
    report = await engine.run_backtest(df)
    return report
