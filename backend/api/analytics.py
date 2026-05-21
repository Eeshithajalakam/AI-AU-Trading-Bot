from fastapi import APIRouter
from api.websockets import ai_service

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("")
async def get_analytics():
    """
    Get AI performance analytics and aggregate signal data.
    """
    return ai_service.analytics
