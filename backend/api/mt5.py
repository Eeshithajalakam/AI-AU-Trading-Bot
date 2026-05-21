from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.websockets import order_manager

router = APIRouter(prefix="/api/mt5", tags=["MT5 Management"])

class AccountSwitchRequest(BaseModel):
    account_type: str

@router.post("/switch-account")
async def switch_mt5_account(request: AccountSwitchRequest):
    """
    Switch the MT5 broker connection between DEMO and LIVE accounts.
    Requires credentials to be set in the .env file.
    """
    account_type = request.account_type.upper()
    if account_type not in ["DEMO", "LIVE"]:
        raise HTTPException(status_code=400, detail="Invalid account type. Use DEMO or LIVE.")
        
    success = order_manager.broker.switch_account(account_type)
    if not success:
        # Provide helpful instructions if connection fails
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to connect to {account_type} account. Ensure MT5 is running on a Windows host and credentials are correct in .env."
        )
        
    return {"status": "success", "message": f"Successfully switched and connected to MT5 {account_type} account."}

@router.get("/status")
async def get_mt5_status():
    """
    Get real-time MT5 connection status and synchronize active trades directly from the broker.
    """
    connected = order_manager.broker.check_connection()
    if not connected:
        return {"status": "disconnected", "account_type": order_manager.broker.current_account_type}
        
    trades = order_manager.broker.sync_active_trades()
    return {
        "status": "connected",
        "account_type": order_manager.broker.current_account_type,
        "active_trades": trades,
        "total_active_trades": len(trades)
    }
